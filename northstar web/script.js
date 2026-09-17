(function () {
  "use strict";

  /* ---------- Footer year ---------- */
  var yearEl = document.getElementById("year");
  if (yearEl) yearEl.textContent = new Date().getFullYear();

  /* ---------- Header height (drives mobile nav-panel offset) ----------
     The mobile nav panel and scrim need to sit exactly below the header.
     Rather than hardcode a pixel value that breaks the moment header
     content wraps to a second line on a narrow phone, measure the real
     rendered header height and expose it as a CSS variable. */
  var header = document.getElementById("site-header");

  function setHeaderHeightVar() {
    if (!header) return;
    document.documentElement.style.setProperty("--header-h", header.offsetHeight + "px");
  }
  setHeaderHeightVar();
  window.addEventListener("resize", setHeaderHeightVar);
  window.addEventListener("orientationchange", setHeaderHeightVar);
  if (document.fonts && document.fonts.ready) {
    document.fonts.ready.then(setHeaderHeightVar);
  }

  /* ---------- Mobile navigation ---------- */
  var navToggle = document.getElementById("nav-toggle");
  var mainNav = document.getElementById("main-nav");
  var navScrim = document.getElementById("nav-scrim");

  function closeNav() {
    navToggle.setAttribute("aria-expanded", "false");
    navToggle.setAttribute("aria-label", "Open menu");
    mainNav.classList.remove("is-open");
    navScrim.classList.remove("is-visible");
    document.body.style.overflow = "";
  }

  function openNav() {
    setHeaderHeightVar();
    navToggle.setAttribute("aria-expanded", "true");
    navToggle.setAttribute("aria-label", "Close menu");
    mainNav.classList.add("is-open");
    navScrim.classList.add("is-visible");
    document.body.style.overflow = "hidden";
  }

  if (navToggle) {
    navToggle.addEventListener("click", function () {
      var isOpen = navToggle.getAttribute("aria-expanded") === "true";
      if (isOpen) closeNav();
      else openNav();
    });
  }

  if (navScrim) navScrim.addEventListener("click", closeNav);

  mainNav.querySelectorAll("a").forEach(function (link) {
    link.addEventListener("click", closeNav);
  });

  window.addEventListener("keydown", function (e) {
    if (e.key === "Escape") closeNav();
  });

  /* ---------- Sticky header shadow on scroll ---------- */
  function onScroll() {
    if (window.scrollY > 8) {
      header.style.boxShadow = "0 2px 12px rgba(18, 32, 44, 0.06)";
    } else {
      header.style.boxShadow = "none";
    }
  }
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  /* ---------- FAQ accordion ---------- */
  var faqQuestions = document.querySelectorAll(".faq-question");
  faqQuestions.forEach(function (btn) {
    var answer = btn.nextElementSibling;
    btn.addEventListener("click", function () {
      var isOpen = btn.getAttribute("aria-expanded") === "true";

      faqQuestions.forEach(function (otherBtn) {
        if (otherBtn !== btn && otherBtn.getAttribute("aria-expanded") === "true") {
          otherBtn.setAttribute("aria-expanded", "false");
          otherBtn.nextElementSibling.style.height = "0px";
        }
      });

      if (isOpen) {
        btn.setAttribute("aria-expanded", "false");
        answer.style.height = "0px";
      } else {
        btn.setAttribute("aria-expanded", "true");
        answer.style.height = answer.scrollHeight + "px";
      }
    });
  });

  /* ---------- Contact form: real submission to the lead API ---------- */
  var form = document.getElementById("case-form");
  var successBox = document.getElementById("form-success");
  var errorBox = document.getElementById("form-error");
  var submitBtn = document.getElementById("case-form-submit");
  var SUBMIT_LABEL_DEFAULT = submitBtn ? submitBtn.textContent : "Submit";
  var API_BASE = window.NORTHSTAR_API_BASE || "http://localhost:8000";

  // The accident-date field can't be set in the future.
  var accidentDateInput = document.getElementById("accidentDate");
  if (accidentDateInput) {
    accidentDateInput.max = new Date().toISOString().slice(0, 10);
  }

  // Maps backend field names (snake_case) back to the form's field names,
  // so a server-side validation error can highlight the right input.
  var BACKEND_FIELD_MAP = {
    first_name: "firstName",
    last_name: "lastName",
    phone: "phone",
    email: "email",
    contact_method: "contactMethod",
    accident_type: "injuryType",
    accident_date: "accidentDate",
    description: "details",
    consent: "consent",
  };

  function setError(field, message) {
    var errorEl = form.querySelector('[data-error-for="' + field.name + '"]');
    var wrapper = field.closest(".form-field");
    if (errorEl) errorEl.textContent = message || "";
    if (wrapper) wrapper.classList.toggle("has-error", !!message);
  }

  function clearFormError() {
    errorBox.hidden = true;
    errorBox.textContent = "";
  }

  function showFormError(message) {
    errorBox.textContent = message;
    errorBox.hidden = false;
  }

  function validateField(field) {
    if (field.hasAttribute("required") === false) {
      setError(field, "");
      return true;
    }

    if (field.type === "checkbox") {
      if (!field.checked) {
        setError(field, "Please check this box to continue.");
        return false;
      }
      setError(field, "");
      return true;
    }

    if (!field.value || !field.value.trim()) {
      setError(field, "This field is required.");
      return false;
    }

    if (field.type === "email") {
      var emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailPattern.test(field.value.trim())) {
        setError(field, "Enter a valid email address.");
        return false;
      }
    }

    if (field.type === "tel") {
      var digits = field.value.replace(/\D/g, "");
      if (digits.length < 10) {
        setError(field, "Enter a valid phone number.");
        return false;
      }
    }

    setError(field, "");
    return true;
  }

  function buildPayload() {
    return {
      first_name: form.firstName.value.trim(),
      last_name: form.lastName.value.trim(),
      phone: form.phone.value.trim(),
      email: form.email.value.trim(),
      contact_method: form.contactMethod.value,
      accident_type: form.injuryType.value,
      accident_date: form.accidentDate.value || null,
      description: form.details.value.trim(),
      consent: form.consent.checked,
    };
  }

  // Applies field-level errors returned by FastAPI's 422 validation
  // response (a list of {loc, msg} entries) back onto the matching inputs.
  function applyServerValidationErrors(detail) {
    var appliedAny = false;
    if (!Array.isArray(detail)) return appliedAny;

    detail.forEach(function (item) {
      var backendField = item.loc && item.loc[item.loc.length - 1];
      var formFieldName = BACKEND_FIELD_MAP[backendField];
      if (!formFieldName) return;
      var input = form.elements[formFieldName];
      if (!input) return;
      setError(input, item.msg || "Please check this field.");
      appliedAny = true;
    });

    return appliedAny;
  }

  function setSubmitting(isSubmitting) {
    if (!submitBtn) return;
    submitBtn.disabled = isSubmitting;
    submitBtn.textContent = isSubmitting ? "Submitting\u2026" : SUBMIT_LABEL_DEFAULT;
  }

  if (form) {
    var requiredFields = form.querySelectorAll("[required]");

    requiredFields.forEach(function (field) {
      field.addEventListener("blur", function () {
        validateField(field);
      });

      // Once a field is showing an error, clear it the moment the field
      // becomes valid rather than waiting for blur. Without this, fixing
      // a field and immediately interacting with whatever sits right
      // below it (e.g. the consent checkbox) causes the error text to
      // collapse at that exact instant, shifting the layout under the
      // user's pointer.
      var liveEvent = field.tagName === "SELECT" || field.type === "checkbox" ? "change" : "input";
      field.addEventListener(liveEvent, function () {
        var wrapper = field.closest(".form-field");
        if (wrapper && wrapper.classList.contains("has-error")) {
          validateField(field);
        }
      });
    });

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      clearFormError();

      var isValid = true;
      requiredFields.forEach(function (field) {
        if (!validateField(field)) isValid = false;
      });

      if (!isValid) {
        var firstError = form.querySelector(".has-error input, .has-error select, .has-error textarea");
        if (firstError) firstError.focus();
        return;
      }

      setSubmitting(true);

      fetch(API_BASE + "/api/leads", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(buildPayload()),
      })
        .then(function (response) {
          return response.json().catch(function () { return null; }).then(function (data) {
            return { ok: response.ok, status: response.status, data: data };
          });
        })
        .then(function (result) {
          if (result.ok && result.data && result.data.success) {
            form.querySelectorAll(".form-field, button[type='submit']").forEach(function (el) {
              el.style.display = "none";
            });
            successBox.hidden = false;
            successBox.focus();
            return;
          }

          // FastAPI validation errors (422) come back as {detail: [...]}
          if (result.status === 422 && result.data && applyServerValidationErrors(result.data.detail)) {
            var firstServerError = form.querySelector(".has-error input, .has-error select, .has-error textarea");
            if (firstServerError) firstServerError.focus();
            showFormError("Please correct the highlighted fields and try again.");
            return;
          }

          var message =
            (result.data && (result.data.detail || result.data.message)) ||
            "Something went wrong while submitting your request. Please try again or call us directly.";
          showFormError(typeof message === "string" ? message : "Something went wrong while submitting your request. Please try again or call us directly.");
        })
        .catch(function () {
          showFormError("Something went wrong while submitting your request. Please try again or call us directly.");
        })
        .finally(function () {
          setSubmitting(false);
        });
    });
  }
})();
