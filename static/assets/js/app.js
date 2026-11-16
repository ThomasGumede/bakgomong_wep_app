/* Bakgomong: DOM enhancement only. Every page has its own actual HTML file and page structure.
 * This is not secure authentication, payment processing, or backend authorisation.
 */
(() => {
  "use strict";
 
  const DEFAULT = window.BAKGOMONG_SAMPLE;
  const CFG = window.BAKGOMONG_CONFIG || {};
  const KEY = "bakgomong-model-frontend-demo-v2",
    WHO = "bakgomong-preview-persona";
  let db = readDb();
  let me = readWho();
  const $ = (s, root = document) => root.querySelector(s);
  const $$ = (s, root = document) => Array.from(root.querySelectorAll(s));
  const htmlEscape = (v) =>
    String(v ?? "").replace(
      /[&<>"']/g,
      (c) =>
        ({
          "&": "&amp;",
          "<": "&lt;",
          ">": "&gt;",
          '"': "&quot;",
          "'": "&#39;",
        })[c],
    );
  const money = (v) =>
    "R " +
    Number(v || 0).toLocaleString("en-ZA", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
  const date = (v) =>
    v
      ? new Date(v.length === 10 ? v + "T12:00:00" : v).toLocaleDateString(
          "en-ZA",
          { day: "2-digit", month: "short", year: "numeric" },
        )
      : "Not set";
  const slug = (v) =>
    String(v)
      .toLowerCase()
      .trim()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-|-$/g, "");
  const moneyNum = (v) => Number(v || 0);
  const sum = (a) => a.reduce((n, v) => n + moneyNum(v), 0);
  const qs = (key) => new URLSearchParams(location.search).get(key);
  const uid = (prefix) =>
    prefix +
    "-" +
    Date.now().toString(36) +
    Math.random().toString(36).slice(2, 6);
  const page = document.body.dataset.page;
  const byId = (type, id) => (db[type] || []).find((x) => x.id === id);
  const account = (id) => byId("accounts", id);
  const family = (id) => byId("families", id);
  const contrib = (id) => byId("contributionTypes", id);
  const mc = (id) => byId("memberContributions", id);
  const paymentFor = (id) =>
    db.payments.find((p) => p.member_contribution === id);
  const fullName = (a) =>
    a ? `${a.first_name || ""} ${a.last_name || ""}`.trim() : "Unknown member";
  const who = () => account(me) || db.accounts[0];
  const isStaff = () =>
    [
      "TREASURER",
      "SECRETARY",
      "CLAN_CHAIRPERSON",
      "KGOSANA",
      "MMAKGOSANA",
      "DEP_SECRETARY",
      "DEP_CHAIRPERSON",
      "DEVELOPER",
    ].includes(who().role);
  const canFinance = () =>
    ["TREASURER", "CLAN_CHAIRPERSON", "DEVELOPER"].includes(who().role);
  const canManage = () => isStaff();
  const roleName = (r) =>
    ({
      MEMBER: "Member",
      KGOSANA: "Kgosana",
      MMAKGOSANA: "Mmakgosana",
      CLAN_CHAIRPERSON: "Chairperson",
      DEP_CHAIRPERSON: "Deputy Chairperson",
      SECRETARY: "Secretary",
      DEP_SECRETARY: "Deputy Secretary",
      TREASURER: "Treasurer",
      SPONSOR: "Sponsor",
      DEVELOPER: "Developer",
    })[r] ||
    r ||
    "—";
  const scopeName = (s) =>
    ({
      clan: "Entire Kgotla",
      family: "Specific family",
      family_leaders: "Family leaders",
      executives: "Executives",
    })[s] ||
    s ||
    "—";
  const recName = (r) =>
    ({ once_off: "Once off", monthly: "Monthly", annual: "Annual" })[r] ||
    r ||
    "—";
  const categoryName = (r) =>
    ({
      event: "Event / celebration",
      burial: "Burial / funeral fund",
      savings: "Savings / stokvel",
      investment: "Investment fund",
      business: "Business project",
      holiday: "Travel fund",
      grocery: "Food club",
      emergency: "Emergency support",
      education: "Education / skills",
      other: "Other",
    })[r] ||
    r ||
    "—";
  const documentCategoryName = (c) =>
    ({
      minutes: "Meeting minutes",
      report: "Financial / contribution report",
      event: "Event notice",
      policy: "Policy / constitution",
      other: "Other",
    })[c] ||
    c ||
    "Other";
  const methodName = (m) =>
    ({
      cash: "Cash",
      bank: "Bank deposit / EFT",
      mobile: "Yoco online",
      other: "Other",
    })[m] ||
    m ||
    "Not selected";
  const paid = (m) => m.is_paid === "PAID";
  const pending = (m) => ["PENDING", "AWAITING APPROVAL"].includes(m.is_paid);
  const labelStatus = (s) =>
    ({
      PAID: "Paid",
      PENDING: "Pending verification",
      NOT_PAID: "Not paid",
      "AWAITING APPROVAL": "Awaiting approval",
      CANCELLED: "Cancelled",
      PARTIALLY_PAID: "Partially paid",
      APPROVED: "Approved",
      REJECTED: "Rejected",
    })[s] ||
    s ||
    "Unknown";
  const status = (s) =>
    `<span class="status ${s === "PAID" || s === "APPROVED" ? "status-green" : s === "PENDING" || s === "AWAITING APPROVAL" ? "status-yellow" : s === "NOT_PAID" || s === "REJECTED" ? "status-red" : "status-gray"}">${htmlEscape(labelStatus(s))}</span>`;
  function readDb() {
    try {
      const v = JSON.parse(localStorage.getItem(KEY));
      if (
        v &&
        Array.isArray(v.accounts) &&
        Array.isArray(v.memberContributions)
      )
        return v;
    } catch {}
    return JSON.parse(JSON.stringify(DEFAULT));
  }
  function save() {
    try {
      localStorage.setItem(KEY, JSON.stringify(db));
    } catch (e) {
      console.warn("Demo storage unavailable", e);
    }
  }
  function readWho() {
    try {
      return sessionStorage.getItem(WHO) || "a1";
    } catch {
      return "a1";
    }
  }
  function setWho(id) {
    me = id;
    try {
      sessionStorage.setItem(WHO, id);
    } catch {}
    location.href = "dashboard.html";
  }
  function toast(msg, error = false) {
    const el = $("#toast");
    if (!el) {
      alert(msg);
      return;
    }
    el.textContent = msg;
    el.classList.toggle("error", !!error);
    el.hidden = false;
    clearTimeout(window.__toastT);
    window.__toastT = setTimeout(() => (el.hidden = true), 4000);
  }
  function sumExpected(data = db.memberContributions) {
    return sum(data.map((m) => m.amount_due));
  }
  function sumPaid(data = db.memberContributions) {
    return sum(data.filter(paid).map((m) => m.amount_due));
  }
  function sumOutstanding(data = db.memberContributions) {
    return sumExpected(data) - sumPaid(data);
  }
  function memberRecords(id) {
    return db.memberContributions.filter((m) => m.account === id);
  }
  function familyRecords(id) {
    return db.memberContributions.filter(
      (m) => account(m.account)?.family === id,
    );
  }
  const initials = (n) =>
    n
      .split(" ")
      .filter(Boolean)
      .slice(0, 2)
      .map((s) => s[0])
      .join("")
      .toUpperCase() || "BK";
  function facts(data) {
    return data
      .map(
        ([k, v]) =>
          `<div><dt>${htmlEscape(k)}</dt><dd>${htmlEscape(v ?? "—")}</dd></div>`,
      )
      .join("");
  }
  function goto(url) {
    location.href = url;
  }
  function optionInto(select, records, labelFn, selected) {
    if (!select) return;
    const defaultOption =
      select.querySelector("option")?.outerHTML ||
      '<option value="">Select</option>';
    select.innerHTML =
      defaultOption +
      records
        .map(
          (x) =>
            `<option value="${htmlEscape(x.id)}" ${selected === x.id ? "selected" : ""}>${htmlEscape(labelFn(x))}</option>`,
        )
        .join("");
  }
  function button(href, title, kind = "outline") {
    return `<a class="btn-${kind} btn-sm" href="${htmlEscape(href)}">${htmlEscape(title)}</a>`;
  }
  function payActions(m, forAll = false) {
    let parts = [
      `<a class="link-inline" href="payment-detail.html?id=${encodeURIComponent(m.id)}">View</a>`,
    ];
    if (paid(m)) {
      parts.push(
        `<button class="link-inline" data-download="receipt" data-id="${htmlEscape(m.id)}">Receipt</button>`,
      );
    } else {
      parts.push(
        `<button class="link-inline" data-download="invoice" data-id="${htmlEscape(m.id)}">Invoice</button>`,
      );
      if (m.account === me && !pending(m))
        parts.push(
          `<a class="link-inline" href="payment-checkout.html?id=${encodeURIComponent(m.id)}">Pay now</a>`,
        );
      if (m.account === me && pending(m))
        parts.push(
          `<a class="link-inline" href="payment-detail.html?id=${encodeURIComponent(m.id)}">Pending</a>`,
        );
      if (forAll && canFinance())
        parts.push(
          `<a class="link-inline" href="log-payment.html?id=${encodeURIComponent(m.id)}">Log payment</a>`,
        );
    }
    return `<div class="row-actions">${parts.join("")}</div>`;
  }
  function tableRows(target, items, render) {
    let host = $("#" + target);
    if (!host) return;
    let count = host.closest("table")?.querySelectorAll("th").length || 5;
    host.innerHTML = items.length
      ? items.map(render).join("")
      : `<tr><td colspan="${count}" class="empty-state">No records match your search.</td></tr>`;
  }
  function setupFilter(render) {
    let input = $("#search-input"),
      primary = $("#filter-main"),
      second = $("#filter-secondary");
    [input, primary, second]
      .filter(Boolean)
      .forEach((el) =>
        el.addEventListener(
          el.tagName === "INPUT" ? "input" : "change",
          render,
        ),
      );
    render();
  }
  function viewSet(id, text) {
    let el = $("#" + id);
    if (el) el.textContent = text;
  }
  function renderShell() {
    let u = who();
    $("[data-user-name]").forEach((el) => (el.textContent = fullName(u)));
    $("[data-user-role]").forEach((el) => (el.textContent = roleName(u.role)));
    $("[data-avatar]").forEach(
      (el) => (el.textContent = initials(fullName(u))),
    );
    $("[data-first-name]").forEach((el) => (el.textContent = u.first_name));
    if ($("#demo-user")) $("#demo-user").value = me;
    $("#demo-user")?.addEventListener("change", (e) => setWho(e.target.value));
    $("#open-sidebar")?.addEventListener("click", () => {
      $("#sidebar")?.classList.add("open");
      $("#sidebar-overlay").hidden = false;
    });
    let close = () => {
      $("#sidebar")?.classList.remove("open");
      if ($("#sidebar-overlay")) $("#sidebar-overlay").hidden = true;
    };
    $("#close-sidebar")?.addEventListener("click", close);
    $("#sidebar-overlay")?.addEventListener("click", close);
    $$(".staff-only").forEach((el) => {
      el.hidden = !isStaff();
    });
    $("#logout-link")?.addEventListener("click", () => {
      try {
        sessionStorage.removeItem(WHO);
      } catch {}
    });
  }
  function renderDashboard() {
    const mine = memberRecords(me),
      unpaid = mine.filter((m) => !paid(m));
    viewSet("dash-paid", money(sumPaid(mine)));
    viewSet("dash-outstanding", money(sumOutstanding(mine)));
    viewSet(
      "dash-upcoming",
      String(
        unpaid.filter(
          (m) =>
            m.due_date && m.due_date >= new Date().toLocaleDateString("en-CA"),
        ).length,
      ),
    );
    const u = who();
    let f = family(u.family);
    viewSet(
      "dash-family-members",
      String(db.accounts.filter((a) => a.family === u.family).length),
    );
    if ($("#dash-family-card"))
      $("#dash-family-card").innerHTML = f
        ? `<div class="dash-family-content"><div class="dash-family-head"><span class="family-icon">${initials(f.name)}</span><div><strong>${htmlEscape(f.name)}</strong><p>Leader: ${htmlEscape(fullName(account(f.leader)))}</p></div></div><a class="family-link" href="family-overview.html?mine=1">Explore my family →</a></div>`
        : '<div class="empty-state">Your family has not been assigned.</div>';
    let upcoming = unpaid
      .slice()
      .sort((a, b) => (a.due_date || "").localeCompare(b.due_date || ""))
      .slice(0, 4);
    if ($("#upcoming-payments"))
      $("#upcoming-payments").innerHTML = upcoming.length
        ? upcoming
            .map(
              (m) =>
                `<div class="due-row"><div><h3>${htmlEscape(contrib(m.contribution_type)?.name || "Contribution")}</h3><p>Due ${htmlEscape(date(m.due_date))} · ${htmlEscape(recName(contrib(m.contribution_type)?.recurrence))}</p></div><div class="row-actions"><strong class="due-amount mono-num">${money(m.amount_due)}</strong>${pending(m) ? button("payment-detail.html?id=" + m.id, "Pending") : button("payment-checkout.html?id=" + m.id, "Pay now", "primary")}</div></div>`,
            )
            .join("")
        : '<p class="empty-state">No upcoming unpaid contributions.</p>';
    const meetings = db.meetings
      .filter((x) => x.meeting_status === "scheduled")
      .slice(0, 2);
    if ($("#dash-meetings"))
      $("#dash-meetings").innerHTML = meetings
        .map(
          (x) =>
            `<div class="meeting-mini"><span class="date-box"><strong>${date(x.meeting_date).slice(0, 2)}</strong><span>${new Date(x.meeting_date).toLocaleDateString("en-ZA", { month: "short" })}</span></span><div><strong>${htmlEscape(x.title)}</strong><p>${htmlEscape(date(x.meeting_date))}</p></div></div>`,
        )
        .join("");
    tableRows(
      "dash-rows",
      mine.slice(0, 4),
      (m) =>
        `<tr><td><strong>${htmlEscape(contrib(m.contribution_type)?.name)}</strong></td><td>${date(m.due_date)}</td><td>${money(m.amount_due)}</td><td>${status(m.is_paid)}</td><td>${payActions(m)}</td></tr>`,
    );
  }
  function renderFamilies() {
    const render = () => {
      let query = ($("#search-input")?.value || "").toLowerCase(),
        filt = $("#filter-main")?.value;
      let arr = db.families.filter((f) => {
        let leader = fullName(account(f.leader));
        return (
          `${f.name} ${leader}`.toLowerCase().includes(query) &&
          (!filt || (filt === "approved") === !!f.is_approved)
        );
      });
      $("#families-list").innerHTML = arr.length
        ? arr
            .map((f) => {
              let members = db.accounts.filter((a) => a.family === f.id);
              let l = account(f.leader);
              return `<article class="family-list-item"><div class="family-card-top"><span class="family-icon">${initials(f.name)}</span>${status(f.is_approved ? "APPROVED" : "PENDING")}</div><div class="family-card-content"><h3>${htmlEscape(f.name)}</h3><p>Registered ${date(f.created)}</p><div class="family-card-stats"><span>Family leader<strong>${htmlEscape(l ? `${l.title} ${fullName(l)}` : "Not assigned")}</strong></span><span>Members<strong>${members.length}</strong></span></div><div class="family-card-footer"><a href="family-overview.html?id=${encodeURIComponent(f.id)}" class="text-link">View family →</a><span style="font-size:10px;color:#98a99c">${htmlEscape(f.slug)}</span></div></div></article>`;
            })
            .join("")
        : '<p class="empty-state">No families found.</p>';
    };
    setupFilter(render);
  }
  function getFamilyForPage() {
    return qs("mine")
      ? family(who().family)
      : family(qs("id")) || db.families[0];
  }
  function renderFamilyOverview() {
    let f = getFamilyForPage();
    if (!f) return;
    viewSet("family-name", f.name);
    viewSet(
      "family-status",
      f.is_approved ? "Approved family branch" : "Pending approval",
    );
    let members = db.accounts.filter((a) => a.family === f.id);
    let ownRecords = familyRecords(f.id);
    viewSet("family-member-count", String(members.length));
    viewSet("family-paid", money(sumPaid(ownRecords)));
    viewSet("family-unpaid", money(sumOutstanding(ownRecords)));
    $("#family-facts").innerHTML = facts([
      ["Family name", f.name],
      ["Family slug", f.slug],
      ["Leader", fullName(account(f.leader))],
      ["Approval", f.is_approved ? "Approved" : "Pending"],
      ["Registered on", date(f.created)],
      ["Family members", members.length],
    ]);
    let l = account(f.leader);
    $("#family-leader-detail").innerHTML = l
      ? `<div class="leader-card"><span class="avatar-initials" style="height:54px;width:54px">${initials(fullName(l))}</span><div><h3>${htmlEscape(l.title + " " + fullName(l))}</h3><p>${htmlEscape(roleName(l.role))} · ${htmlEscape(l.email)}</p><p>${l.is_family_leader ? "Designated family leader" : "Leader assigned through Family.leader"}</p></div></div>`
      : '<p class="empty-state">Family leader has not been assigned.</p>';
    if (canManage())
      $("#family-actions").innerHTML = button(
        "member-form.html?family=" + encodeURIComponent(f.id),
        "Add member",
        "primary",
      );
    let draw = () => {
      let q = ($("#family-members-search")?.value || "").toLowerCase();
      tableRows(
        "family-member-rows",
        members.filter((a) => fullName(a).toLowerCase().includes(q)),
        (a) =>
          `<tr><td><strong>${htmlEscape(fullName(a))}</strong><span class="sub">${htmlEscape(a.username)}</span></td><td>${htmlEscape(a.title || "—")}</td><td>${htmlEscape(roleName(a.role))}</td><td>${htmlEscape(a.member_classification || "—")}</td><td>${status(a.is_approved ? "APPROVED" : "PENDING")}</td><td><a class="link-inline" href="account.html?id=${encodeURIComponent(a.id)}">View</a></td></tr>`,
      );
    };
    $("#family-members-search")?.addEventListener("input", draw);
    draw();
  }
  function renderMembers() {
    const draw = () => {
      let q = ($("#search-input")?.value || "").toLowerCase(),
        role = $("#filter-main")?.value,
        st = $("#filter-secondary")?.value;
      let list = db.accounts.filter(
        (a) =>
          `${fullName(a)} ${a.username} ${a.email} ${family(a.family)?.name || ""}`
            .toLowerCase()
            .includes(q) &&
          (!role || a.role === role) &&
          (!st || (st === "approved") === !!a.is_approved),
      );
      tableRows(
        "member-rows",
        list,
        (a) =>
          `<tr><td><div class="person-inline"><span class="avatar-initials">${initials(fullName(a))}</span><div><strong>${htmlEscape(fullName(a))}</strong><span class="sub">${htmlEscape(a.email)}</span></div></div></td><td>${htmlEscape(family(a.family)?.name || "—")}</td><td>${htmlEscape(a.title)}</td><td>${htmlEscape(roleName(a.role))}</td><td>${status(a.is_approved ? "APPROVED" : "PENDING")}</td><td><a class="link-inline" href="account.html?id=${encodeURIComponent(a.id)}">View</a></td></tr>`,
      );
    };
    setupFilter(draw);
  }
  function renderAccount() {
    // In production, the backend MUST enforce permission for requested ids.
    let a = qs("id") && canManage() ? account(qs("id")) : who();
    if (!a) return;
    viewSet("account-full-name", `${a.title || ""} ${fullName(a)}`);
    viewSet("account-handle", "@" + a.username);
    $("#account-roles").innerHTML =
      `<div class="badge-line">${status(a.is_approved ? "APPROVED" : "PENDING")}<span class="status status-blue">${htmlEscape(roleName(a.role))}</span></div>`;
    $("#account-facts").innerHTML = facts([
      ["Username", a.username],
      ["Email", a.email],
      [
        "ID number",
        a.id_number ? "•••• " + a.id_number.slice(-4) : "Not supplied",
      ],
      ["Phone", a.phone || "Not supplied"],
      ["Title", a.title],
      ["Gender", a.gender],
      ["Maiden name", a.maiden_name || "Not supplied"],
      ["Date of birth", date(a.birth_date)],
      ["Address", a.address || "Not supplied"],
      ["Languages", a.langueges_spoken || "Not supplied"],
      ["Biography", a.biography || "Not supplied"],
    ]);
    $("#account-membership").innerHTML = facts([
      ["Family", family(a.family)?.name || "Not assigned"],
      ["Kgotla role", roleName(a.role)],
      ["Classification", a.member_classification],
      ["Employment", a.employment_status],
      ["Family leader", a.is_family_leader ? "Yes" : "No"],
      ["Approved", a.is_approved ? "Yes" : "No"],
      ["Joined", date(a.created)],
    ]);
    tableRows(
      "account-payment-rows",
      memberRecords(a.id),
      (m) =>
        `<tr><td><strong>${htmlEscape(contrib(m.contribution_type)?.name || "")}</strong></td><td>${money(m.amount_due)}</td><td>${date(m.due_date)}</td><td>${status(m.is_paid)}</td><td>${payActions(m)}</td></tr>`,
    );
  }
  function formValues(form) {
    const v = {};
    new FormData(form).forEach((value, key) => {
      if (value instanceof File) {
        v[key] = value.name || "";
      } else v[key] = value;
    });
    $$("input[type=checkbox]", form).forEach((e) => (v[e.name] = e.checked));
    return v;
  }
  function fillForm(form, obj) {
    Object.entries(obj || {}).forEach(([k, v]) => {
      const el = form.elements.namedItem(k);
      if (!el || !("value" in el)) return;
      if (el.type === "checkbox") el.checked = !!v;
      else el.value = v ?? "";
    });
  }
  function addFormHandler(id, type, handler) {
    let el = $("#" + id);
    if (!el) return;
    el.addEventListener("submit", (e) => {
      e.preventDefault();
      try {
        handler(formValues(el), el);
      } catch (err) {
        console.error(err);
        toast(err.message || "Could not save the preview record.", true);
      }
    });
  }
  function requireManager() {
    if (!canManage()) {
      toast(
        "Manager role is required in the live application. Use demo role switcher to preview.",
        true,
      );
      return false;
    }
    return true;
  }
  function renderFamilyForm() {
    optionInto($("#leader"), db.accounts, (a) => `${a.title} ${fullName(a)}`);
    addFormHandler("family-form", "family", (v) => {
      if (!requireManager()) return;
      let f = {
        id: uid("f"),
        name: v.name.trim(),
        slug: slug(v.name),
        leader: v.leader || null,
        is_approved: !!v.is_approved,
        created: new Date().toISOString().slice(0, 10),
      };
      if (
        db.families.some((z) => z.name.toLowerCase() === f.name.toLowerCase())
      )
        throw Error("This family name already exists.");
      db.families.push(f);
      if (f.leader) {
        let l = account(f.leader);
        l.family = f.id;
        l.is_family_leader = true;
      }
      save();
      goto("family-overview.html?id=" + f.id);
    });
  }
  function renderMemberForm() {
    if (!requireManager()) return;
    optionInto($("#family"), db.families, (f) => f.name, qs("family"));
    addFormHandler("member-form", "account", (v) => {
      if (!v.username || !v.email)
        throw Error("Username and email are required.");
      let id = uid("a");
      let a = {
        id,
        username: v.username,
        first_name: v.first_name,
        last_name: v.last_name,
        email: v.email,
        phone: v.phone || "",
        title: v.title || "",
        gender: v.gender || "",
        maiden_name: "",
        biography: v.biography || "",
        id_number: "",
        birth_date: v.birth_date || "",
        employment_status: v.employment_status || "",
        member_classification: v.member_classification || "",
        langueges_spoken: "",
        address: v.address || "",
        family: v.family || null,
        role: v.role || "MEMBER",
        is_approved: !!v.is_approved,
        is_family_leader: !!v.is_family_leader,
        created: new Date().toISOString().slice(0, 10),
      };
      db.accounts.push(a);
      save();
      goto("members.html");
    });
  }
  function renderAccountEdit() {
    let a = who();
    fillForm($("#account-edit-form"), a);
    addFormHandler("account-edit-form", "account", (v) => {
      for (let k of [
        "first_name",
        "last_name",
        "email",
        "phone",
        "title",
        "gender",
        "maiden_name",
        "birth_date",
        "employment_status",
        "langueges_spoken",
        "address",
        "biography",
      ])
        a[k] = v[k] || "";
      save();
      goto("account.html");
    });
  }
  function renderChangePassword() {
    addFormHandler("change-password-form", "account", (v) => {
      if (v.new_password !== v.confirm_password) {
        toast("New passwords do not match.", true);
        return;
      }
      if (v.new_password.length < 10) {
        toast("Use a password of at least 10 characters.", true);
        return;
      }
      $("#change-password-form").reset();
      toast(
        "Preview only: no password was changed or stored. Connect Django’s authenticated change-password view.",
        true,
      );
    });
  }
  function eligibility(ct) {
    // Preview mirrors current contributions/signals.py recipient conditions.
    // In the source signal, Q(children) and Q(developer/sponsor) evaluates to the second Q;
    // recipients below therefore exclude developer/sponsor roles (flagged in README).
    return db.accounts.filter(
      (a) =>
        a.is_active !== false &&
        a.is_approved &&
        !["DEVELOPER", "SPONSOR"].includes(a.role) &&
        (ct.scope === "clan" ||
          (ct.scope === "family" && a.family === ct.family) ||
          (ct.scope === "family_leaders" && a.is_family_leader) ||
          (ct.scope === "executives" &&
            [
              "CLAN_CHAIRPERSON",
              "KGOSANA",
              "SECRETARY",
              "DEP_SECRETARY",
              "TREASURER",
              "DEP_CHAIRPERSON",
            ].includes(a.role))),
    );
  }
  function defaultDueDate(recurrence) {
    const d = new Date();
    d.setHours(12, 0, 0, 0);
    if (recurrence === "monthly") {
      const orig = d.getDate();
      d.setDate(1);
      d.setMonth(d.getMonth() + 1);
      const cap = new Date(d.getFullYear(), d.getMonth() + 1, 0).getDate();
      d.setDate(Math.min(orig, cap));
    } else if (recurrence === "annual") d.setFullYear(d.getFullYear() + 1);
    else d.setDate(d.getDate() + 7);
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  }
  function renderContributions() {
    let expected = sumExpected(),
      collected = sumPaid();
    viewSet("contrib-expected", money(expected));
    viewSet("contrib-paid", money(collected));
    viewSet("contrib-outstanding", money(expected - collected));
    const draw = () => {
      let q = ($("#search-input")?.value || "").toLowerCase(),
        scope = $("#filter-main")?.value,
        st = $("#filter-secondary")?.value;
      let rows = db.contributionTypes.filter(
        (c) =>
          `${c.name} ${c.description}`.toLowerCase().includes(q) &&
          (!scope || scope === c.scope) &&
          (!st || (st === "active") === !!c.is_active),
      );
      tableRows("contrib-rows", rows, (c) => {
        let m = db.memberContributions.filter(
          (x) => x.contribution_type === c.id,
        );
        return `<tr><td><strong>${htmlEscape(c.name)}</strong><span class="sub">${htmlEscape(categoryName(c.category))}</span></td><td>${htmlEscape(scopeName(c.scope))}</td><td>${htmlEscape(recName(c.recurrence))}</td><td>${money(c.amount)}</td><td>${money(sumExpected(m))}</td><td>${money(sumPaid(m))}</td><td><a class="link-inline" href="contribution-overview.html?id=${encodeURIComponent(c.id)}">View overview</a></td></tr>`;
      });
    };
    setupFilter(draw);
  }
  function renderContributionOverview() {
    let c = contrib(qs("id")) || db.contributionTypes[0];
    if (!c) return;
    viewSet("ct-name", c.name);
    viewSet("ct-description", c.description || "No description");
    viewSet("ct-default-amount", money(c.amount));
    $("#ct-badges").innerHTML =
      `<span class="status status-green">${htmlEscape(categoryName(c.category))}</span><span class="status status-blue">${htmlEscape(scopeName(c.scope))}</span>`;
    let records = db.memberContributions.filter(
        (m) => m.contribution_type === c.id,
      ),
      expected = sumExpected(records),
      collected = sumPaid(records),
      pct = expected ? Math.round((collected / expected) * 100) : 0;
    viewSet("ct-expected", money(expected));
    viewSet("ct-paid", money(collected));
    viewSet("ct-outstanding", money(expected - collected));
    viewSet("ct-percent", pct + "%");
    $("#ct-progress-bar").style.width = pct + "%";
    $("#ct-facts").innerHTML = facts([
      ["Name", c.name],
      ["Description", c.description],
      ["Category", categoryName(c.category)],
      ["Amount per member", money(c.amount)],
      ["Scope", scopeName(c.scope)],
      ["Frequency", recName(c.recurrence)],
      ["Family", c.family ? family(c.family)?.name : "All applicable families"],
      ["Default due date", date(c.due_date)],
      ["Created by", fullName(account(c.created_by))],
      ["Active", c.is_active ? "Yes" : "No"],
      ["Created on", date(c.created)],
    ]);
    let draw = () => {
      let q = ($("#ct-members-search")?.value || "").toLowerCase();
      tableRows(
        "ct-member-rows",
        records.filter((x) =>
          fullName(account(x.account)).toLowerCase().includes(q),
        ),
        (m) =>
          `<tr><td><strong>${htmlEscape(fullName(account(m.account)))}</strong></td><td>${htmlEscape(family(account(m.account)?.family)?.name || "—")}</td><td>${date(m.due_date)}</td><td>${money(m.amount_due)}</td><td>${status(m.is_paid)}</td><td>${payActions(m, true)}</td></tr>`,
      );
    };
    $("#ct-members-search")?.addEventListener("input", draw);
    draw();
  }
  function renderContributionForm() {
    if (!requireManager()) return;
    optionInto($("#family"), db.families, (f) => f.name);
    addFormHandler("contribution-form", "contribution", (v) => {
      if (!v.name || moneyNum(v.amount) <= 0)
        throw Error("Name and a valid amount are required.");
      if (v.scope === "family" && !v.family)
        throw Error("Select a family for family-scope contributions.");
      if (!["clan", "family_leaders", "family", "executives"].includes(v.scope))
        throw Error("Select a contribution scope.");
      let c = {
        id: uid("c"),
        name: v.name,
        slug: slug(v.name),
        description: v.description || "",
        category: v.category || "other",
        family: v.scope === "family" ? v.family : null,
        amount: Number(v.amount),
        recurrence: v.recurrence || "once_off",
        scope: v.scope,
        due_date: v.due_date || null,
        created_by: me,
        is_active: !!v.is_active,
        created: new Date().toISOString().slice(0, 10),
      };
      db.contributionTypes.push(c);
      let due = c.due_date || defaultDueDate(c.recurrence);
      let eligible = eligibility(c);
      eligible.forEach((a) =>
        db.memberContributions.push({
          id: uid("mc"),
          account: a.id,
          contribution_type: c.id,
          amount_due: c.amount,
          due_date: due,
          reference:
            "MC-DEMO-" + Math.random().toString(36).slice(2, 10).toUpperCase(),
          is_paid: "NOT_PAID",
          created: new Date().toISOString().slice(0, 10),
        }),
      );
      save();
      goto("contribution-overview.html?id=" + c.id);
    });
  }
  function renderPaymentSummaries() {
    let items =
      page === "my-payments"
        ? memberRecords(me)
        : canFinance()
          ? db.memberContributions
          : memberRecords(me);
    viewSet("payments-paid", money(sumPaid(items)));
    viewSet("payments-outstanding", money(sumOutstanding(items)));
    viewSet("payments-count", String(items.length));
    return items;
  }
  function renderPayments() {
    let items = renderPaymentSummaries();
    const draw = () => {
      let q = ($("#search-input")?.value || "").toLowerCase(),
        st = $("#filter-main")?.value;
      let list = items.filter(
        (m) =>
          `${fullName(account(m.account))} ${contrib(m.contribution_type)?.name || ""} ${m.reference}`
            .toLowerCase()
            .includes(q) &&
          (!st || m.is_paid === st),
      );
      tableRows(
        "payment-rows",
        list,
        (m) =>
          `<tr><td><strong>${htmlEscape(fullName(account(m.account)))}</strong></td><td>${htmlEscape(contrib(m.contribution_type)?.name || "")}</td><td>${date(m.due_date)}</td><td>${money(m.amount_due)}</td><td>${status(m.is_paid)}</td><td>${payActions(m, true)}</td></tr>`,
      );
    };
    setupFilter(draw);
  }
  function renderMyPayments() {
    let items = renderPaymentSummaries();
    let draw = () => {
      let q = ($("#search-input")?.value || "").toLowerCase(),
        st = $("#filter-main")?.value;
      let records = items.filter(
        (m) =>
          `${contrib(m.contribution_type)?.name} ${m.reference}`
            .toLowerCase()
            .includes(q) &&
          (!st || m.is_paid === st),
      );
      tableRows("my-payment-rows", records, (m) => {
        let p = paymentFor(m.id);
        return `<tr><td><strong>${htmlEscape(contrib(m.contribution_type)?.name || "")}</strong><span class="sub">${htmlEscape(m.reference)}</span></td><td>${date(m.due_date)}</td><td>${money(m.amount_due)}</td><td>${htmlEscape(p ? p.payment_method_type || methodName(p.payment_method) : "—")}</td><td>${status(m.is_paid)}</td><td>${payActions(m)}</td></tr>`;
      });
    };
    setupFilter(draw);
  }
  function memberPayment() {
    let m = mc(qs("id"));
    if (!m) {
      toast("Payment record not found", true);
      return null;
    }
    if (m.account !== me && !canFinance()) {
      toast("This payment belongs to another member.", true);
      return null;
    }
    return m;
  }
  function renderPaymentDetail() {
    let m = memberPayment();
    if (!m) return;
    let c = contrib(m.contribution_type),
      a = account(m.account),
      p = paymentFor(m.id);
    viewSet("pd-name", c?.name || "Contribution");
    viewSet("pd-member", fullName(a));
    viewSet("pd-amount", money(m.amount_due));
    $("#pd-status").outerHTML = status(m.is_paid).replace(
      "<span",
      '<span id="pd-status"',
    );
    $("#payment-facts").innerHTML = facts([
      ["Member", fullName(a)],
      ["Payment reference", m.reference],
      ["Due date", date(m.due_date)],
      ["Amount due", money(m.amount_due)],
      ["Payment status", labelStatus(m.is_paid)],
      [
        "Payment channel",
        p
          ? p.payment_method_type || methodName(p.payment_method)
          : "Not selected",
      ],
      ["Payment date", p ? date(p.payment_date) : "Not paid"],
      ["Payment reference (bank)", p?.reference || "Not supplied"],
      ["Receipt number", p?.receipt || "Not issued"],
      [
        "Verification",
        p?.is_approved ? labelStatus(p.is_approved) : "Awaiting payment",
      ],
      [
        "Recorded by",
        p?.recorded_by ? fullName(account(p.recorded_by)) : "Not recorded",
      ],
    ]);
    $("#payment-contribution-facts").innerHTML = facts([
      ["Title", c?.name],
      ["Category", categoryName(c?.category)],
      ["Scope", scopeName(c?.scope)],
      ["Frequency", recName(c?.recurrence)],
      ["Default amount", money(c?.amount)],
      ["Description", c?.description || "—"],
    ]);
    let actions = [
      `<button type="button" class="btn-primary" data-download="${paid(m) ? "receipt" : "invoice"}" data-id="${htmlEscape(m.id)}">Download ${paid(m) ? "receipt" : "invoice"}</button>`,
    ];
    if (m.account === me && !paid(m) && !pending(m))
      actions.push(button("payment-checkout.html?id=" + m.id, "Pay now"));
    if (m.account === me && pending(m))
      actions.push(
        button("payment-instructions.html?id=" + m.id, "View instructions"),
      );
    if (canFinance() && !paid(m))
      actions.push(button("log-payment.html?id=" + m.id, "Log payment"));
    if (canFinance() && p && p.is_approved === "PENDING")
      actions.push(
        `<button class="btn-outline" type="button" data-payment-preview-approve="${htmlEscape(m.id)}">Preview approve</button>`,
      );
    $("#payment-actions").innerHTML = actions.join("");
  }
  function checkoutSummary(m) {
    let c = contrib(m.contribution_type);
    return `<div><span>Contribution</span><strong>${htmlEscape(c?.name || "")}</strong></div><div><span>Scope · Frequency</span><strong>${htmlEscape(scopeName(c?.scope))} · ${htmlEscape(recName(c?.recurrence))}</strong></div><div><span>Amount due</span><strong>${money(m.amount_due)}</strong></div>`;
  }
  function renderCheckout() {
    let m = memberPayment();
    if (!m) return;
    if (paid(m) || pending(m)) {
      goto("payment-detail.html?id=" + m.id);
      return;
    }
    viewSet("checkout-title", contrib(m.contribution_type)?.name);
    $("#checkout-summary").innerHTML = checkoutSummary(m);
    $("#checkout-form")?.addEventListener("submit", (e) => {
      e.preventDefault();
      let type = $("input[name=method]:checked")?.value || "eft";
      if (type === "yoco") {
        goto("yoco-checkout.html?id=" + m.id);
        return;
      }
      createPending(m, type);
      goto("payment-instructions.html?id=" + m.id + "&method=" + type);
    });
  }
  function createPending(m, method) {
    if (paid(m)) throw Error("This contribution is already verified as paid.");
    if (pending(m) && paymentFor(m.id)) return paymentFor(m.id);
    let p = paymentFor(m.id);
    let val = method === "yoco" ? "mobile" : "bank";
    if (!p) {
      p = {
        id: uid("p"),
        account: m.account,
        member_contribution: m.id,
        amount: moneyNum(m.amount_due),
        payment_method: val,
        payment_method_type:
          method === "eft"
            ? "EFT"
            : method === "bank"
              ? "Bank deposit"
              : "Yoco",
        reference: null,
        receipt: null,
        payment_date: new Date().toISOString().slice(0, 10),
        recorded_by: null,
        payment_verified_by: null,
        is_approved: "PENDING",
      };
      db.payments.push(p);
    }
    m.is_paid = "AWAITING APPROVAL";
    save();
    return p;
  }
  function renderInstructions() {
    let m = memberPayment();
    if (!m) return;
    let c = contrib(m.contribution_type),
      p = paymentFor(m.id),
      type = qs("method") || p?.payment_method_type?.toLowerCase() || "eft";
    viewSet("instruction-title", c?.name || "Contribution payment");
    viewSet(
      "instruction-subtitle",
      `Reference ${m.reference} · ${scopeName(c?.scope)}`,
    );
    $("#instruction-member-info").innerHTML = checkoutSummary(m);
    $("#bank-facts").innerHTML = facts([
      ["Bank name", CFG.bankName || "Not configured"],
      ["Account name", CFG.accountName || "Not configured"],
      ["Account number", CFG.accountNumber || "Not configured"],
      ["Branch code", CFG.branchCode || "Not configured"],
      ["Reference to use", m.reference],
      ["Amount", money(m.amount_due)],
      ["Send proof to", CFG.proofEmail || "Not configured"],
    ]);
    $("#instruction-channel-note").innerHTML =
      `<strong>${htmlEscape(type === "bank" ? "Bank deposit" : type === "yoco" ? "Yoco payment" : "EFT / bank transfer")} instructions</strong><p>${type === "bank" ? "Deposit the exact amount at the bank, use the reference above and send a clear image of your bank-stamped slip to the confirmed Kgotla email." : type === "yoco" ? "The Yoco handoff will be linked to a verified backend session. This preview only shows a pending record." : "Use the reference above for your bank transfer, then email proof of payment to the confirmed Kgotla email. The Treasurer will verify the payment."}</p>`;
    $("#instruction-details-link").href = "payment-detail.html?id=" + m.id;
    $("#download-invoice")?.addEventListener("click", () =>
      downloadDoc(m, "invoice"),
    );
  }
  function renderYoco() {
    let m = memberPayment();
    if (!m) return;
    let back = $("#back-yoco");
    if (back) back.href = "payment-checkout.html?id=" + m.id;
    let b = $("#preview-yoco"),
      url = CFG.yocoCheckoutUrl;
    if (!b) return;
    if (url && /^https:\/\//.test(url)) {
      b.textContent = "Continue to hosted checkout";
      b.addEventListener("click", () => location.assign(url));
    } else
      b.addEventListener("click", () => {
        createPending(m, "yoco");
        goto("payment-detail.html?id=" + m.id);
      });
  }
  function renderLogPayment() {
    if (!canFinance()) {
      toast("Only finance managers can log a payment.", true);
      $("#log-payment-form")
        ?.querySelector("button[type=submit]")
        ?.setAttribute("disabled", "true");
      return;
    }
    const eligible = db.memberContributions.filter((m) => !paid(m));
    optionInto(
      $("#member_contribution"),
      eligible,
      (m) =>
        `${fullName(account(m.account))} · ${contrib(m.contribution_type)?.name} · ${money(m.amount_due)}`,
      qs("id"),
    );
    const pre = mc(qs("id"));
    if (pre) $("#amount").value = pre.amount_due;
    $("#member_contribution")?.addEventListener("change", (e) => {
      $("#amount").value = mc(e.target.value)?.amount_due || "";
    });
    addFormHandler("log-payment-form", "payment", (v) => {
      let m = mc(v.member_contribution);
      if (!m) throw Error("Select a member contribution.");
      if (paid(m)) throw Error("Already paid.");
      if (who().role === "TREASURER" && !v.proof_of_payment)
        throw Error(
          "Please select the proof-of-payment file (preview stores its filename only).",
        );
      let p = paymentFor(m.id);
      if (!p) {
        p = {
          id: uid("p"),
          account: m.account,
          member_contribution: m.id,
          amount: Number(v.amount),
          payment_method: v.payment_method,
          reference: v.reference,
          receipt: v.receipt || null,
          proof_of_payment: v.proof_of_payment || null,
          payment_method_type:
            v.payment_method === "bank"
              ? "EFT / Bank deposit"
              : methodName(v.payment_method),
          payment_date: new Date().toISOString().slice(0, 10),
          recorded_by: me,
          payment_verified_by: null,
          is_approved: "PENDING",
        };
        db.payments.push(p);
      } else {
        p.amount = Number(v.amount);
        p.reference = v.reference;
        p.receipt = v.receipt || null;
        p.proof_of_payment = v.proof_of_payment || null;
        p.payment_method = v.payment_method;
        p.recorded_by = me;
        p.is_approved = "PENDING";
      }
      m.is_paid = "AWAITING APPROVAL";
      save();
      goto("payment-detail.html?id=" + m.id);
    });
  }
  function downloadDoc(m, type) {
    let c = contrib(m.contribution_type),
      a = account(m.account),
      p = paymentFor(m.id);
    if (type === "receipt" && !paid(m)) {
      toast("Receipt is available only for verified paid contributions.", true);
      return;
    }
    let docTitle =
      type === "receipt" ? "Payment receipt" : "Contribution invoice";
    let rows = [
      ["Member", fullName(a)],
      ["Contribution", c?.name],
      ["Scope", scopeName(c?.scope)],
      ["Frequency", recName(c?.recurrence)],
      ["Due date", date(m.due_date)],
      ["Amount", money(m.amount_due)],
      ["Member contribution reference", m.reference],
      ["Status", labelStatus(m.is_paid)],
    ];
    if (p) {
      rows.push(
        [
          "Payment method",
          p.payment_method_type || methodName(p.payment_method),
        ],
        ["Payment date", date(p.payment_date)],
        ["Bank transaction reference", p.reference || "Not yet supplied"],
        ["Receipt number", p.receipt || "Not yet issued"],
        ["Verified", p.is_approved === "APPROVED" ? "Yes" : "No"],
      );
    }
    if (type === "invoice")
      rows.push(
        ["Bank details", CFG.accountNumber || "Contact Treasurer"],
        ["Proof email", CFG.proofEmail || "Contact Secretary"],
      );
    let markup = `<!doctype html><html lang="en"><head><meta charset="utf-8"><title>${docTitle}</title><style>body{font:14px Arial,sans-serif;color:#203b31;max-width:740px;margin:45px auto;padding:0 25px}h1{color:#1d684c}header{display:flex;justify-content:space-between;border-bottom:3px solid #247c5c;padding-bottom:20px}header small{color:#658372}table{width:100%;border-collapse:collapse;margin-top:30px}td{border-bottom:1px solid #dde9df;padding:12px 5px}td:first-child{color:#829487;width:42%}strong{color:#25533b}.note{background:#f0f7f1;padding:15px;margin-top:30px;font-size:12px}.print{margin-top:30px;border:0;padding:12px;background:#247c5c;color:white}@media print{.print{display:none}}</style></head><body><header><div><strong>BAKGOMONG</strong><br><small>KGOTLA YA MALLA</small></div><div>${docTitle.toUpperCase()}<br><small>Frontend preview · illustrative only</small></div></header><h1>${docTitle}</h1><table>${rows.map(([k, v]) => `<tr><td>${htmlEscape(k)}</td><td><strong>${htmlEscape(v || "—")}</strong></td></tr>`).join("")}</table><div class="note">${type === "receipt" ? "Demo receipt for a member contribution already marked PAID in the sample data. This is not evidence of a real payment." : "Demo invoice. Do not make a payment to unverified bank details. Payments remain pending until verified by your Kgotla Treasurer."}</div><button class="print" onclick="window.print()">Print / Save as PDF</button></body></html>`;
    let blob = new Blob([markup], { type: "text/html;charset=utf-8" }),
      url = URL.createObjectURL(blob),
      link = document.createElement("a");
    link.href = url;
    link.download = type + "-" + (m.reference || m.id) + ".html";
    document.body.append(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 5000);
    toast(
      `Downloaded a printable ${type} (HTML). Open it and print to save as PDF.`,
    );
  }
  function renderReports() {
    let expected = sumExpected(),
      collected = sumPaid(),
      expenses = sum(db.expenses.map((e) => e.amount)),
      opening = moneyNum(db.kgotlaBalance.balance);
    viewSet("report-net", money(opening + collected - expenses));
    viewSet("report-bank", money(opening));
    viewSet("report-paid", money(collected));
    viewSet("report-expenses", money(expenses));
    viewSet("report-families", db.families.length + " / " + db.accounts.length);
    viewSet(
      "report-percent",
      (expected ? Math.round((collected / expected) * 100) : 0) + "%",
    );
    viewSet(
      "report-outstanding-percent",
      (expected ? Math.round(((expected - collected) / expected) * 100) : 0) +
        "%",
    );
    $("#report-bar").style.width =
      (expected ? Math.min(100, (collected / expected) * 100) : 0) + "%";
    viewSet("report-total-expected", money(expected));
    viewSet("report-total-outstanding", money(expected - collected));
    tableRows(
      "expense-rows",
      db.expenses,
      (e) =>
        `<tr><td><strong>${htmlEscape(e.title)}</strong></td><td>${date(e.incurred_date || e.incurred_on)}</td><td>Entire Kgotla</td><td>${money(e.amount)}</td><td>${status(e.approved ? "APPROVED" : "PENDING")}</td><td>${htmlEscape(e.description || "—")}</td></tr>`,
    );
    // KgotlaExpense has no Family foreign key. This section identifies only records explicitly mentioning family.
    const familyExpenses = db.expenses.filter((e) =>
      /\bfamil(?:y|ies)\b/i.test(`${e.title} ${e.description || ""}`),
    );
    tableRows(
      "family-expense-rows",
      familyExpenses,
      (e) =>
        `<tr><td><strong>${htmlEscape(e.title)}</strong><span class="sub">${htmlEscape(e.description || "—")}</span></td><td>${date(e.incurred_date)}</td><td>${money(e.amount)}</td><td>${status(e.approved ? "APPROVED" : "PENDING")}</td></tr>`,
    );
    viewSet(
      "family-expense-sum",
      money(sum(familyExpenses.map((e) => e.amount))),
    );
  }
  function renderExpenseForm() {
    if (!canFinance()) return;
    addFormHandler("expense-form", "expense", (v) => {
      if (Number(v.amount) <= 0) throw Error("Amount must be positive");
      db.expenses.push({
        id: uid("e"),
        title: v.title,
        amount: Number(v.amount),
        description: v.description,
        added_by: me,
        incurred_date: v.incurred_date,
        recurring: v.recurring || "once_off",
        approved: !!v.approved,
      });
      save();
      goto("reports.html");
    });
  }
  function allowedDoc(d) {
    return (
      d.visibility === "clan" ||
      (d.visibility === "family" && d.family === who().family) ||
      (d.visibility === "private" &&
        ["CLAN_CHAIRPERSON", "DEVELOPER"].includes(who().role))
    );
  }
  function renderDocuments() {
    let draw = () => {
      let q = ($("#search-input")?.value || "").toLowerCase(),
        cat = $("#filter-main")?.value,
        vis = $("#filter-secondary")?.value;
      let records = db.documents.filter(
        (d) =>
          allowedDoc(d) &&
          `${d.title} ${d.description}`.toLowerCase().includes(q) &&
          (!cat || cat === d.category) &&
          (!vis || vis === d.visibility),
      );
      $("#documents-list").innerHTML = records.length
        ? records
            .map(
              (d) =>
                `<article class="document-item"><span class="document-icon">PDF</span><div><h3>${htmlEscape(d.title)}</h3><p>${htmlEscape(d.description || "")}</p></div><div class="document-tags"><span class="status status-blue">${htmlEscape(documentCategoryName(d.category))}</span><span class="status status-gray">${htmlEscape(d.visibility)}</span></div><div class="document-bottom"><small>${date(d.created)}</small><button class="link-inline" data-document="${htmlEscape(d.id)}">${d.file ? "Download" : "View details"}</button></div></article>`,
            )
            .join("")
        : '<p class="empty-state">No documents found for your access level.</p>';
    };
    setupFilter(draw);
  }
  function renderDocumentForm() {
    if (!requireManager()) return;
    optionInto($("#family"), db.families, (f) => f.name);
    addFormHandler("document-form", "document", (v) => {
      if (v.visibility === "family" && !v.family)
        throw Error("Please choose a family.");
      db.documents.push({
        id: uid("d"),
        title: v.title,
        description: v.description || "",
        category: v.category || "other",
        visibility: v.visibility || "clan",
        family: v.visibility === "family" ? v.family : null,
        file: null,
        uploaded_by: me,
        created: new Date().toISOString().slice(0, 10),
      });
      save();
      goto("documents.html");
    });
  }
  function canSeeMeeting(m) {
    return (
      m.audience === "clan" ||
      (m.audience === "family" && m.family === who().family) ||
      (m.audience === "family_leaders" && who().is_family_leader) ||
      (m.audience === "executives" && isStaff())
    );
  }
  function renderMeetings() {
    let draw = () => {
      let q = ($("#search-input")?.value || "").toLowerCase(),
        typ = $("#filter-main")?.value,
        st = $("#filter-secondary")?.value;
      let arr = db.meetings.filter(
        (m) =>
          canSeeMeeting(m) &&
          `${m.title} ${m.meeting_venue || ""}`.toLowerCase().includes(q) &&
          (!typ || m.meeting_type === typ) &&
          (!st || m.meeting_status === st),
      );
      $("#meetings-list").innerHTML = arr.length
        ? arr
            .map((m) => {
              let dt = new Date(m.meeting_date);
              return `<article class="meeting-item"><div class="date-box"><strong>${dt.getDate()}</strong><span>${dt.toLocaleDateString("en-ZA", { month: "short" })}</span></div><div><span class="section-kicker">${htmlEscape(scopeName(m.audience))}</span><h3>${htmlEscape(m.title)}</h3><p>${htmlEscape(m.description || "")}</p><p>◷ ${htmlEscape(date(m.meeting_date))} · ${dt.toLocaleTimeString("en-ZA", { hour: "2-digit", minute: "2-digit" })} · ${htmlEscape(m.meeting_type === "online" ? "Online" : m.meeting_venue || "Venue to confirm")}</p>${status(m.meeting_status === "scheduled" ? "PENDING" : m.meeting_status === "completed" ? "PAID" : "CANCELLED")}</div></article>`;
            })
            .join("")
        : '<p class="empty-state">No meetings match your search.</p>';
    };
    setupFilter(draw);
  }
  function renderMeetingForm() {
    if (!requireManager()) return;
    optionInto($("#family"), db.families, (f) => f.name);
    addFormHandler("meeting-form", "meeting", (v) => {
      if (v.meeting_type === "online" && !v.meeting_link)
        throw Error("Online meetings require a meeting link.");
      if (v.meeting_type === "in_person" && !v.meeting_venue)
        throw Error("In-person meetings require a venue.");
      if (v.audience === "family" && !v.family)
        throw Error("Select a family for family-audience meetings.");
      if (new Date(v.meeting_end_date) <= new Date(v.meeting_date))
        throw Error("End time must follow start time.");
      db.meetings.push({
        id: uid("m"),
        title: v.title,
        description: v.description || "",
        meeting_type: v.meeting_type,
        meeting_venue: v.meeting_type === "in_person" ? v.meeting_venue : null,
        meeting_link: v.meeting_type === "online" ? v.meeting_link : null,
        audience: v.audience || "clan",
        family: v.audience === "family" ? v.family : null,
        meeting_date: v.meeting_date,
        meeting_end_date: v.meeting_end_date,
        meeting_status: "scheduled",
        created_by: me,
      });
      save();
      goto("meetings.html");
    });
  }
  function setupDownloads() {
    document.addEventListener("click", (e) => {
      const approval = e.target.closest("[data-payment-preview-approve]");
      if (approval) {
        e.preventDefault();
        let m = mc(approval.dataset.paymentPreviewApprove),
          p = m && paymentFor(m.id);
        if (!canFinance() || !p || p.is_approved !== "PENDING") {
          toast(
            "Only a finance preview account can approve an eligible preview payment.",
            true,
          );
          return;
        }
        p.is_approved = "APPROVED";
        p.payment_verified_by = me;
        p.payment_verified_date = new Date().toISOString();
        m.is_paid =
          Number(p.amount) >= Number(m.amount_due) ? "PAID" : "PARTIALLY_PAID";
        save();
        toast(
          "Preview record approved locally. No real funds or payment verification occurred.",
        );
        renderPaymentDetail();
        return;
      }
      const d = e.target.closest("[data-download]");
      if (d) {
        e.preventDefault();
        let m = mc(d.dataset.id);
        if (m) downloadDoc(m, d.dataset.download);
        return;
      }
      const doc = e.target.closest("[data-document]");
      if (doc) {
        let x = byId("documents", doc.dataset.document);
        toast(
          x?.file
            ? "Connect a Django media URL to download this document."
            : "This sample document has no uploaded file. Django storage integration is pending.",
        );
      }
    });
  }
  function setupLogin() {
    $("#login-form")?.addEventListener("submit", (e) => {
      e.preventDefault();
      setWho($("#login-persona")?.value || "a1");
    });
  }
  renderShell();
  setupDownloads();
  const pages = {
    dashboard: renderDashboard,
    families: renderFamilies,
    "family-overview": renderFamilyOverview,
    "family-form": renderFamilyForm,
    members: renderMembers,
    "member-form": renderMemberForm,
    account: renderAccount,
    "account-edit": renderAccountEdit,
    "change-password": renderChangePassword,
    contributions: renderContributions,
    "contribution-overview": renderContributionOverview,
    "contribution-form": renderContributionForm,
    payments: renderPayments,
    "my-payments": renderMyPayments,
    "payment-detail": renderPaymentDetail,
    "payment-checkout": renderCheckout,
    "payment-instructions": renderInstructions,
    "yoco-checkout": renderYoco,
    "log-payment": renderLogPayment,
    reports: renderReports,
    "expense-form": renderExpenseForm,
    documents: renderDocuments,
    "document-form": renderDocumentForm,
    meetings: renderMeetings,
    "meeting-form": renderMeetingForm,
    login: setupLogin,
  };




  try {
    pages[page]?.();
  } catch (e) {
    console.error("Page init error:", e);
    toast("Some demonstration content could not load: " + e.message, true);
  }
})();
