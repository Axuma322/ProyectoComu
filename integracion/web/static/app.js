"use strict";
const role = document.body.dataset.role;
const token = document.querySelector('meta[name="comu-token"]').content;
const feedback = document.querySelector("#feedback");
const connection = document.querySelector("#connection-status");
let images = [];

function message(text, error = false) {
  feedback.textContent = text;
  feedback.dataset.error = String(error);
}

async function api(url, options = {}) {
  const response = await fetch(url, {
    ...options, cache: "no-store", signal: AbortSignal.timeout(10000),
    headers: { "X-Comu-Token": token, ...options.headers }
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "No se pudo completar la solicitud local.");
  return data;
}

async function refreshState() {
  try {
    const data = await api("/api/estado");
    connection.textContent = `Servidor ${data.rol.toUpperCase()} accesible · integración de imágenes por radio pendiente.`;
    if (role === "tx") {
      document.querySelector("#saved-selection").textContent = data.seleccion
        ? `Guardado en TX: ${data.seleccion.etiqueta} · ${data.seleccion.modo === "sin_perdidas" ? "sin pérdidas" : "con pérdidas"}.`
        : "Todavía no hay una selección guardada en TX.";
    }
  } catch (error) {
    connection.textContent = "Sin respuesta del servidor local. Comprueba Wi-Fi y que Flask siga en ejecución.";
  }
}

if (role === "tx") {
  const select = document.querySelector("#stored-image");
  const save = document.querySelector("#save-selection");
  const preview = document.querySelector("#preview");

  function showPreview() {
    const image = images.find(item => item.nombre === select.value);
    save.disabled = !image;
    preview.hidden = true;
    document.querySelector("#preview-empty").hidden = Boolean(image);
    document.querySelector("#image-details").textContent = image
      ? `${image.ancho} × ${image.alto} píxeles · ${image.bytes} bytes del archivo original.` : "";
    if (image) {
      preview.src = `/imagenes/${encodeURIComponent(image.nombre)}/vista.png`;
    } else {
      preview.removeAttribute("src");
    }
  }
  preview.addEventListener("load", () => { preview.hidden = false; });
  preview.addEventListener("error", () => {
    preview.hidden = true;
    message("No se pudo cargar la vista previa. Comprueba el servidor y la imagen.", true);
  });

  async function refreshImages(preferred) {
    images = (await api("/api/imagenes")).imagenes;
    select.replaceChildren(new Option(images.length ? "Selecciona una imagen…" : "No hay imágenes válidas en TX", ""));
    for (const image of images) select.add(new Option(image.etiqueta, image.nombre));
    if (preferred && images.some(image => image.nombre === preferred)) select.value = preferred;
    showPreview();
  }

  select.addEventListener("change", showPreview);
  document.querySelector("#upload-form").addEventListener("submit", async event => {
    event.preventDefault();
    const button = event.target.querySelector("button");
    button.disabled = true;
    message("Guardando la imagen en la Raspberry TX…");
    try {
      const data = await api("/api/imagenes", { method: "POST", body: new FormData(event.target) });
      await refreshImages(data.imagen.nombre);
      message("Imagen guardada en TX. No se ha enviado al receptor.");
      event.target.reset();
    } catch (error) { message(error.message, true); }
    finally { button.disabled = false; }
  });
  save.addEventListener("click", async () => {
    save.disabled = true;
    try {
      const data = await api("/api/seleccion", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ imagen: select.value, modo: document.querySelector('input[name="mode"]:checked').value })
      });
      message(data.mensaje);
      await refreshState();
    } catch (error) { message(error.message, true); }
    finally { save.disabled = !select.value; }
  });
  (async () => {
    try {
      const state = await api("/api/estado");
      if (state.seleccion) document.querySelector(`input[value="${state.seleccion.modo}"]`).checked = true;
      await refreshImages(state.seleccion?.imagen);
    } catch (error) { message("No se pudo leer la lista de imágenes. Recarga al recuperar la conexión.", true); }
  })();
}

// Consulta el servidor web, no el estado del hardware. Sin tráfico entre las Pi.
(async function poll() {
  await refreshState();
  setTimeout(poll, 5000);
})();
