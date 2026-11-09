(() => {
  let token = null;
  const status = document.getElementById("status");
  async function request(path, options = {}) {
    const headers = {"Content-Type": "application/json"};
    if (token) headers.Authorization = "Bearer " + token;
    const response = await fetch(path, {...options, headers});
    const body = await response.json();
    if (!response.ok) throw new Error(body.error || "Request failed");
    return body;
  }
  document.getElementById("login").addEventListener("submit", async event => {
    event.preventDefault();
    status.textContent = "";
    try {
      const session = await request("/api/sessions", {
        method: "POST",
        body: JSON.stringify({
          email: document.getElementById("email").value,
          password: document.getElementById("password").value
        })
      });
      token = session.token;
      document.getElementById("password").value = "";
      const account = await request("/api/me");
      const invoices = await request("/api/invoices");
      document.getElementById("identity").textContent = "Signed in as " + account.email;
      const list = document.getElementById("invoices");
      list.replaceChildren();
      for (const invoice of invoices.invoices) {
        const li = document.createElement("li");
        const button = document.createElement("button");
        button.type = "button";
        button.textContent = invoice.id;
        button.addEventListener("click", async () => {
          try {
            const record = await request("/api/invoices/" + encodeURIComponent(invoice.id));
            document.getElementById("record").textContent = JSON.stringify(record, null, 2);
          } catch (error) { status.textContent = error.message; }
        });
        li.append(button);
        list.append(li);
      }
      if (!invoices.invoices.length) list.textContent = "No invoices.";
      document.getElementById("workspace").hidden = false;
      document.getElementById("login").hidden = true;
    } catch (error) {
      token = null;
      status.textContent = error.message;
    }
  });
  document.getElementById("logout").addEventListener("click", async () => {
    try { await request("/api/logout", {method: "POST"}); }
    catch (error) { status.textContent = error.message; }
    finally {
      token = null;
      document.getElementById("record").textContent = "";
      document.getElementById("invoices").replaceChildren();
      document.getElementById("workspace").hidden = true;
      document.getElementById("login").hidden = false;
    }
  });
})();
