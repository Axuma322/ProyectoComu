"use strict";
// Cliente de la Raspberry actual: no envía HTTP a la otra Pi ni inventa progreso.
// Las métricas vienen del worker; las imágenes de la galería viven en RX.
const role = document.body.dataset.role;
const token = document.querySelector('meta[name="comu-token"]').content;
const feedback = document.querySelector("#feedback");
const connection = document.querySelector("#connection-status");
let images = [];
let radioAvailable = false;
let linkBusy = false;
let localBusy = false;
let txAction = false;
let dipOk = false;
let received = [];
let selectedReceived = null;
let followLatest = true;
const deletingReceived = new Set();
const modeLabel = mode => ({sin_perdidas: 'Huffman sin pérdidas', con_perdidas: 'cuantización con pérdidas', automatico: 'automático'})[mode] || mode;
const phaseLabel = phase => ({esperando: 'Listo para transmitir', escuchando: 'Esperando una imagen', codificando: 'Codificando imagen', enviando: 'Transmitiendo imagen', recibiendo: 'Recibiendo imagen', completado: 'Transferencia completada', error: 'La transferencia falló', proceso_radio_detenido: 'El proceso de radio está detenido', iniciando_radio: 'Iniciando radio'})[phase] || phase;
const number = (value, digits = 2) => Number(value).toLocaleString('es', {maximumFractionDigits: digits});

function message(text, error = false) {
  feedback.textContent = text;
  feedback.dataset.error = String(error);
}

async function api(url, options = {}) {
  // Esta espera limita una petición HTTP, no la duración de un envío por nRF24.
  const response = await fetch(url, {
    ...options, cache: "no-store", signal: AbortSignal.timeout(10000),
    headers: { "X-Comu-Token": token, ...options.headers }
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "No se pudo completar la solicitud local.");
  return data;
}

function renderMetrics(target, metrics) {
  const wasOpen = target.querySelector('details')?.open || false;
  target.replaceChildren();
  if (!metrics) { target.textContent = 'Sin métricas guardadas.'; return; }
  const list = document.createElement('dl');
  list.className = 'metrics';
  function row(label, value) {
    const term = document.createElement('dt');
    term.textContent = label;
    const detail = document.createElement('dd');
    detail.textContent = value;
    list.append(term, detail);
  }
  const m = metrics;
  if (m.modo) row('Algoritmo', modeLabel(m.modo));
  if (m.bits != null) row('Cuantización', `${m.bits} bits por píxel`);
  if (m.bytes_original != null) row('Archivo original', `${number(m.bytes_original, 0)} bytes`);
  if (m.bytes_comprimidos != null) row('Archivo codificado', `${number(m.bytes_comprimidos, 0)} bytes`);
  if (m.razon_compresion != null) row('Razón de compresión', `${number(m.razon_compresion)} : 1`);
  if (m.total_tx_ms != null) row('Tiempo total TX', `${number(m.total_tx_ms / 1000)} s`);
  if (m.recepcion_ms != null) row('Tiempo de recepción', `${number(m.recepcion_ms / 1000)} s`);
  if (m.compresion_ms != null) row('Compresión', `${number(m.compresion_ms)} ms`);
  if (m.descompresion_ms != null) row('Descompresión en RX', `${number(m.descompresion_ms)} ms`);
  if (m.mse_tx != null) row('MSE (calculado en TX)', number(m.mse_tx, 4));
  if (m.psnr_tx_db != null) row('PSNR (calculado en TX)', `${number(m.psnr_tx_db)} dB`);
  else if (m.mse_tx === 0) row('PSNR (calculado en TX)', '∞ · sin error');
  if (m.reintentos_aplicacion != null) row('Reintentos de aplicación', number(m.reintentos_aplicacion, 0));
  if (m.reintentos_hardware != null) row('Reintentos del radio', number(m.reintentos_hardware, 0));
  if (m.confirmado_por_rx) row('Confirmación de RX', 'Imagen validada y guardada');
  if (m.sha256_verificado) row('Integridad SHA-256', 'Verificada');
  target.append(list);
  const details = document.createElement('details');
  details.open = wasOpen;
  const summary = document.createElement('summary');
  summary.textContent = 'Ver todos los datos';
  const raw = document.createElement('pre');
  raw.textContent = JSON.stringify(metrics, null, 2);
  details.append(summary, raw);
  target.append(details);
}

function updateTxButtons() {
  const hasImage = Boolean(document.querySelector('#stored-image').value);
  document.querySelector('#encode-local').disabled = !hasImage || !dipOk || localBusy || txAction;
  document.querySelector('#delete-image').disabled = !hasImage || linkBusy || localBusy || txAction;
}

function showReceived() {
  const selected = received.find(item => item.nombre === selectedReceived);
  const image = document.querySelector('#received-preview');
  image.hidden = !selected;
  document.querySelector('#received-empty').hidden = Boolean(selected);
  document.querySelector('#received-title').textContent = selected ? `${selected.etiqueta} · ${selected.ancho} × ${selected.alto} píxeles` : '';
  if (selected) {
    if (image.getAttribute('src') !== selected.url) image.src = selected.url;
    image.alt = `Imagen recibida: ${selected.etiqueta}`;
  } else image.removeAttribute('src');
  renderMetrics(document.querySelector('#received-metrics'), selected?.metricas);
  for (const card of document.querySelectorAll('.image-card')) card.classList.toggle('selected', card.dataset.name === selectedReceived);
}

async function refreshReceived(latest) {
  // Conservar la elección de una imagen histórica salvo que se siga la última.
  received = (await api('/api/recibidas')).imagenes;
  if (followLatest || !received.some(item => item.nombre === selectedReceived)) {
    selectedReceived = received.some(item => item.nombre === latest?.nombre) ? latest.nombre : (received[0]?.nombre || null);
    followLatest = true;
  }
  document.querySelector('#received-count').textContent = received.length ? `${received.length} ${received.length === 1 ? 'imagen guardada' : 'imágenes guardadas'}` : 'Todavía no hay imágenes guardadas.';
  const gallery = document.querySelector('#received-gallery');
  const signature = JSON.stringify(received);
  if (gallery.dataset.signature !== signature) {
    gallery.dataset.signature = signature;
    gallery.replaceChildren();
    for (const item of received) {
      const card = document.createElement('article');
      card.className = 'image-card';
      card.dataset.name = item.nombre;
      const thumb = document.createElement('img');
      thumb.src = item.url;
      thumb.loading = 'lazy';
      thumb.alt = item.etiqueta;
      const title = document.createElement('h3');
      title.textContent = item.etiqueta;
      const info = document.createElement('p');
      info.className = 'hint';
      info.textContent = `${item.ancho} × ${item.alto} · ${new Date(item.guardada_en * 1000).toLocaleString()}`;
      const view = document.createElement('button');
      view.textContent = 'Ver imagen y métricas';
      view.addEventListener('click', () => {
        selectedReceived = item.nombre;
        followLatest = received[0]?.nombre === item.nombre;
        showReceived();
      });
      const remove = document.createElement('button');
      remove.className = 'danger';
      remove.textContent = 'Borrar imagen';
      remove.disabled = deletingReceived.has(item.nombre);
      remove.addEventListener('click', async () => {
        if (!window.confirm(`¿Borrar «${item.etiqueta}» de RX?`)) return;
        deletingReceived.add(item.nombre);
        remove.disabled = true;
        try {
          const result = await api(`/api/recibidas/${encodeURIComponent(item.nombre)}`, {method: 'DELETE'});
          message(result.mensaje);
          await refreshState();
        } catch (error) { message(error.message, true); }
        finally { deletingReceived.delete(item.nombre); remove.disabled = false; }
      });
      card.append(thumb, title, info, view, remove);
      gallery.append(card);
    }
  }
  showReceived();
}

async function refreshState() {
  try {
    const data = await api('/api/estado');
    connection.textContent = `Servidor ${data.rol.toUpperCase()} accesible · ${data.radio_integrado ? 'radio activo' : 'radio detenido'}.`;
    const state = data.enlace;
    document.querySelector('#link-state').textContent = state.error || phaseLabel(state.estado);
    document.querySelector('#link-progress').value = state.progreso || 0;
    if (role === 'tx') {
      radioAvailable = data.radio_integrado;
      linkBusy = ['codificando', 'enviando'].includes(state.estado);
      localBusy = data.codificacion?.estado === 'codificando';
      // Modo que usará el botón, tal como lo leen los switches
      const dip = state.dip;
      const dipText = document.querySelector('#dip-mode');
      dipOk = Boolean(dip) && radioAvailable;
      dipText.dataset.off = String(!dipOk);
      if (!dipOk) dipText.textContent = 'No se leen los switches (el enlace debe correr con --gpio).';
      else if (dip.modo === 'con_perdidas') dipText.textContent = `Con pérdidas · ${dip.bits} bits por píxel`;
      else dipText.textContent = modeLabel(dip.modo)[0].toUpperCase() + modeLabel(dip.modo).slice(1);
      updateTxButtons();
      renderMetrics(document.querySelector('#link-metrics'), data.metricas);
      document.querySelector('#saved-selection').textContent = data.seleccion ? `Imagen que enviará el botón: ${data.seleccion.etiqueta}.` : 'Todavía no hay imagen elegida.';
      const codec = data.codificacion;
      document.querySelector('#codec-status').textContent = codec ? (codec.error || `Codificación local: ${codec.estado}`) : 'No se ha probado la compresión local.';
      if (codec?.estado === 'completado') {
        const image = document.querySelector('#codec-preview');
        const url = codec.vista + '?v=' + codec.metricas.sha256_reconstruida;
        if (image.getAttribute('src') !== url) image.src = url;
        image.hidden = false;
        const download = document.querySelector('#codec-download');
        download.href = codec.descarga;
        download.hidden = false;
        renderMetrics(document.querySelector('#codec-metrics'), codec.metricas);
      } else {
        document.querySelector('#codec-preview').hidden = true;
        document.querySelector('#codec-download').hidden = true;
        document.querySelector('#codec-metrics').replaceChildren();
      }
    } else await refreshReceived(data.ultima_imagen);
  } catch (error) {
    connection.textContent = 'Sin respuesta del servidor local. Comprueba Wi-Fi y que Flask siga en ejecución.';
    if (role === 'tx') { radioAvailable = false; updateTxButtons(); }
  }
}

if (role === 'tx') {
  const select = document.querySelector('#stored-image');
  const preview = document.querySelector('#preview');
  function showPreview() {
    const image = images.find(item => item.nombre === select.value);
    updateTxButtons();
    preview.hidden = true;
    document.querySelector('#preview-empty').hidden = Boolean(image);
    document.querySelector('#image-details').textContent = image ? `${image.ancho} × ${image.alto} píxeles · ${image.bytes} bytes del archivo original.` : '';
    if (image) preview.src = `/imagenes/${encodeURIComponent(image.nombre)}/vista.png`;
    else preview.removeAttribute('src');
  }
  preview.addEventListener('load', () => { preview.hidden = false; });
  preview.addEventListener('error', () => {
    preview.hidden = true;
    message('No se pudo cargar la vista previa. Comprueba el servidor y la imagen.', true);
  });
  async function refreshImages(preferred) {
    images = (await api('/api/imagenes')).imagenes;
    select.replaceChildren(new Option(images.length ? 'Selecciona una imagen…' : 'No hay imágenes válidas en TX', ''));
    for (const image of images) select.add(new Option(image.etiqueta, image.nombre));
    if (preferred && images.some(image => image.nombre === preferred)) select.value = preferred;
    showPreview();
  }
  async function chooseImage() {
    // Elegir en la lista ya la deja lista para el botón
    showPreview();
    if (!select.value) return;
    try { message((await api('/api/seleccion', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({imagen: select.value})})).mensaje); }
    catch (error) { message(error.message, true); }
    finally { await refreshState(); }
  }
  select.addEventListener('change', chooseImage);
  document.querySelector('#upload-form').addEventListener('submit', async event => {
    event.preventDefault();
    const button = event.target.querySelector('button');
    button.disabled = true;
    message('Guardando la imagen en TX…');
    try {
      const data = await api('/api/imagenes', {method: 'POST', body: new FormData(event.target)});
      await refreshImages(data.imagen.nombre);
      await chooseImage();
      event.target.reset();
    } catch (error) { message(error.message, true); }
    finally { button.disabled = false; }
  });
  document.querySelector('#delete-image').addEventListener('click', async () => {
    const item = images.find(image => image.nombre === select.value);
    if (!item || !window.confirm(`¿Borrar «${item.etiqueta}» de TX?`)) return;
    txAction = true;
    updateTxButtons();
    try {
      const result = await api(`/api/imagenes/${encodeURIComponent(item.nombre)}`, {method: 'DELETE'});
      message(result.mensaje);
      await refreshImages();
    } catch (error) { message(error.message, true); }
    finally { txAction = false; await refreshState(); }
  });
  document.querySelector('#encode-local').addEventListener('click', async () => {
    txAction = true;
    updateTxButtons();
    try { message((await api('/api/codificar', {method: 'POST'})).mensaje); }
    catch (error) { message(error.message, true); }
    finally { txAction = false; await refreshState(); }
  });
  (async () => {
    try {
      const state = await api('/api/estado');
      await refreshImages(state.seleccion?.imagen);
    } catch (error) { message('No se pudo leer la lista de imágenes. Recarga al recuperar la conexión.', true); }
  })();
}
(async function poll() {
  // Programar después de terminar evita acumular consultas si la web va lenta.
  await refreshState();
  setTimeout(poll, 3000);
})();
