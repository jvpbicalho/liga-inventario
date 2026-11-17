const cfg = window.LIGA_CONFIG;
const $ = (seletor) => document.querySelector(seletor);
let usuario = null;

// ---------- login: authorization code + PKCE no Cognito ----------

function base64url(bytes) {
  return btoa(String.fromCharCode(...new Uint8Array(bytes)))
    .replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

async function entrar() {
  const verifier = base64url(crypto.getRandomValues(new Uint8Array(32)));
  const challenge = base64url(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(verifier)));
  sessionStorage.setItem("pkce_verifier", verifier);
  const params = new URLSearchParams({
    response_type: "code",
    client_id: cfg.clientId,
    redirect_uri: cfg.redirectUri,
    scope: "openid email",
    code_challenge_method: "S256",
    code_challenge: challenge,
  });
  location.href = `${cfg.cognitoDomain}/oauth2/authorize?${params}`;
}

async function trocarCodigoPorToken(code) {
  const corpo = new URLSearchParams({
    grant_type: "authorization_code",
    client_id: cfg.clientId,
    code,
    redirect_uri: cfg.redirectUri,
    code_verifier: sessionStorage.getItem("pkce_verifier") || "",
  });
  const r = await fetch(`${cfg.cognitoDomain}/oauth2/token`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: corpo,
  });
  if (!r.ok) throw new Error("Falha no login: " + (await r.text()));
  const tokens = await r.json();
  sessionStorage.setItem("id_token", tokens.id_token);
  sessionStorage.removeItem("pkce_verifier");
}

function sair() {
  sessionStorage.clear();
  location.href = `${cfg.cognitoDomain}/logout?` +
    new URLSearchParams({ client_id: cfg.clientId, logout_uri: cfg.redirectUri });
}

function lerToken() {
  const token = sessionStorage.getItem("id_token");
  if (!token) return null;
  const payload = JSON.parse(atob(token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/")));
  if (payload.exp * 1000 < Date.now()) {
    sessionStorage.removeItem("id_token");
    return null;
  }
  const grupos = payload["cognito:groups"] || [];
  return { token, sub: payload.sub, email: payload.email, admin: grupos.includes("admin") };
}

// ---------- chamadas à API ----------

async function api(metodo, caminho, corpo) {
  const headers = { Authorization: "Bearer " + usuario.token };
  if (corpo) headers["Content-Type"] = "application/json";
  const r = await fetch(cfg.apiUrl + caminho, {
    method: metodo,
    headers,
    body: corpo ? JSON.stringify(corpo) : undefined,
  });
  if (r.status === 401) {
    sessionStorage.removeItem("id_token");
    entrar();
    throw new Error("Sessão expirada, entrando de novo...");
  }
  const texto = await r.text();
  const dados = texto ? JSON.parse(texto) : null;
  if (!r.ok) throw new Error((dados && (dados.erro || dados.message)) || `Erro ${r.status}`);
  return dados;
}

async function enviarFoto(itemId, arquivo) {
  const { uploadUrl } = await api("POST", `/itens/${encodeURIComponent(itemId)}/foto`);
  // a foto vai direto para o S3, sem passar pela API
  const r = await fetch(uploadUrl, { method: "PUT", headers: { "Content-Type": "image/jpeg" }, body: arquivo });
  if (!r.ok) throw new Error("Falha no envio da foto para o S3");
}

// ---------- tela ----------

function avisar(texto, erro = false) {
  const aviso = $("#aviso");
  aviso.textContent = texto;
  aviso.className = erro ? "erro" : "";
}

async function executar(acao, mensagemOk) {
  try {
    avisar("Aguarde...");
    await acao();
    avisar(mensagemOk);
    await carregar();
  } catch (e) {
    avisar(e.message, true);
  }
}

function botao(texto, aoClicar, classe = "") {
  const b = document.createElement("button");
  b.textContent = texto;
  if (classe) b.className = classe;
  b.addEventListener("click", aoClicar);
  return b;
}

function cartao(item) {
  const el = document.createElement("article");
  el.className = "item";
  const id = encodeURIComponent(item.itemId);

  const foto = document.createElement("div");
  foto.className = "foto";
  if (item.miniaturaUrl) {
    const img = document.createElement("img");
    img.src = item.miniaturaUrl;
    img.alt = item.nome;
    img.addEventListener("error", () => { foto.textContent = "Miniatura em processamento"; });
    foto.append(img);
  } else {
    foto.textContent = "Sem foto";
  }

  const corpo = document.createElement("div");
  corpo.className = "corpo";
  const nome = document.createElement("div");
  nome.className = "nome";
  nome.textContent = item.nome;
  const meta = document.createElement("div");
  meta.className = "meta";
  const categoria = document.createElement("span");
  categoria.textContent = item.categoria || "outros";
  const status = document.createElement("span");
  status.className = "chip " + item.status;
  status.textContent = item.status === "disponivel" ? "Disponível" : "Emprestado";
  meta.append(categoria, status);

  const acoes = document.createElement("div");
  acoes.className = "acoes";
  if (item.status === "disponivel") {
    acoes.append(botao("Pedir empréstimo", () =>
      executar(() => api("POST", `/itens/${id}/emprestimo`), `Você pegou "${item.nome}".`), "primario"));
  } else if (item.emprestadoPara === usuario.sub || usuario.admin) {
    acoes.append(botao("Devolver", () =>
      executar(() => api("POST", `/itens/${id}/devolucao`), `"${item.nome}" foi devolvido.`)));
  }

  corpo.append(nome, meta, acoes);

  if (usuario.admin) {
    const editar = document.createElement("form");
    editar.className = "editar";
    editar.hidden = true;
    const campoNome = document.createElement("input");
    campoNome.value = item.nome;
    campoNome.required = true;
    const campoCategoria = document.createElement("input");
    campoCategoria.value = item.categoria || "";
    const salvar = document.createElement("button");
    salvar.type = "submit";
    salvar.textContent = "Salvar";
    salvar.className = "primario";
    editar.append(campoNome, campoCategoria, salvar);
    editar.addEventListener("submit", (ev) => {
      ev.preventDefault();
      executar(() => api("PUT", `/itens/${id}`, { nome: campoNome.value, categoria: campoCategoria.value }),
        "Item atualizado.");
    });

    const trocarFoto = document.createElement("label");
    trocarFoto.className = "botao";
    trocarFoto.textContent = "Trocar foto";
    const arquivo = document.createElement("input");
    arquivo.type = "file";
    arquivo.accept = "image/jpeg";
    arquivo.hidden = true;
    arquivo.addEventListener("change", () => {
      if (!arquivo.files[0]) return;
      executar(async () => {
        await enviarFoto(item.itemId, arquivo.files[0]);
        await new Promise((ok) => setTimeout(ok, 4000)); // tempo para a Lambda gerar a miniatura
      }, "Foto enviada.");
    });
    trocarFoto.append(arquivo);

    acoes.append(
      botao("Editar", () => { editar.hidden = !editar.hidden; }),
      trocarFoto,
      botao("Apagar", () => {
        if (confirm(`Apagar "${item.nome}"?`)) executar(() => api("DELETE", `/itens/${id}`), "Item apagado.");
      }, "perigo"),
    );
    corpo.append(editar);
  }

  el.append(foto, corpo);
  return el;
}

async function carregar() {
  const itens = await api("GET", "/itens");
  itens.sort((a, b) => a.nome.localeCompare(b.nome, "pt-BR"));
  const lista = $("#lista");
  lista.replaceChildren(...itens.map(cartao));
  if (!itens.length) lista.innerHTML = '<p class="vazio">Nenhum item cadastrado ainda.</p>';
}

$("#form-novo").addEventListener("submit", (ev) => {
  ev.preventDefault();
  const arquivo = $("#novo-foto").files[0];
  executar(async () => {
    const item = await api("POST", "/itens", { nome: $("#novo-nome").value, categoria: $("#novo-categoria").value });
    if (arquivo) {
      await enviarFoto(item.itemId, arquivo);
      await new Promise((ok) => setTimeout(ok, 4000));
    }
    $("#form-novo").reset();
  }, "Item cadastrado.");
});
$("#entrar").addEventListener("click", entrar);
$("#sair").addEventListener("click", sair);

async function iniciar() {
  const code = new URLSearchParams(location.search).get("code");
  if (code) {
    try {
      await trocarCodigoPorToken(code);
    } catch (e) {
      alert(e.message);
    }
    history.replaceState(null, "", location.pathname);
  }
  usuario = lerToken();
  if (!usuario) {
    $("#tela-login").hidden = false;
    return;
  }
  $("#usuario").hidden = false;
  $("#email").textContent = usuario.email;
  $("#papel").textContent = usuario.admin ? "admin" : "membro";
  $("#papel").className = "chip " + (usuario.admin ? "admin" : "membro");
  $("#painel-admin").hidden = !usuario.admin;
  $("#tela-app").hidden = false;
  try {
    await carregar();
  } catch (e) {
    avisar(e.message, true);
  }
}

iniciar();
