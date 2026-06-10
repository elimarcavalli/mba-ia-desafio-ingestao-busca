/*
 * Inline field-level validation for the Chainlit login form.
 *
 * Chainlit 2.11.1's bundled login form (react-hook-form) only honors the
 * `auth.login.form.<field>.required` translation keys — it has no min-length
 * or pattern rules. This script adds DOM-level validation that mimics the
 * native error UX (red border + small destructive-coloured message under the
 * input) so users see the rule violation as they type, instead of having to
 * submit and read a generic banner.
 *
 * Mirrors the server-side rules from
 * src/application/use_cases/authenticate_or_register_user.py:
 *   username regex: ^[a-zA-Z0-9._@+-]{2,64}$
 *   password min length: 6
 */
(function () {
  "use strict";

  var USERNAME_RE = /^[a-zA-Z0-9._@+\-]{2,64}$/;
  var MIN_PASSWORD = 6;
  var MAX_USERNAME = 64;
  var ERROR_CLASS = "docmind-inline-error";
  var INPUT_INVALID_CLASS = "border-destructive";

  var MESSAGES = {
    usernameTooShort: "Username must be at least 2 characters",
    usernameTooLong: "Username must be at most 64 characters",
    usernameInvalidChars:
      "Username may only contain letters, numbers and . _ @ + -",
    passwordTooShort: "Password must be at least 6 characters",
  };

  function validateUsername(value) {
    if (!value) return null; // empty handled by Chainlit's required rule
    if (value.length < 2) return MESSAGES.usernameTooShort;
    if (value.length > MAX_USERNAME) return MESSAGES.usernameTooLong;
    if (!USERNAME_RE.test(value)) return MESSAGES.usernameInvalidChars;
    return null;
  }

  function validatePassword(value) {
    if (!value) return null; // empty handled by Chainlit's required rule
    if (value.length < MIN_PASSWORD) return MESSAGES.passwordTooShort;
    return null;
  }

  function ensureErrorNode(input) {
    // Place the message right after the input's wrapper, matching Chainlit's
    // own pattern: <p class="text-sm text-destructive">{message}</p>
    // Password input lives inside a `relative` wrapper; email input does not.
    var anchor = input.parentElement;
    if (
      anchor &&
      anchor.classList &&
      anchor.classList.contains("relative")
    ) {
      anchor = anchor.parentElement || anchor;
    }
    if (!anchor) return null;

    // Reuse our own node if already present.
    var existing = anchor.querySelector(
      "p." + ERROR_CLASS + '[data-for="' + input.id + '"]'
    );
    if (existing) return existing;

    var p = document.createElement("p");
    p.className = "text-sm text-destructive " + ERROR_CLASS;
    p.setAttribute("data-for", input.id);
    p.style.display = "none";
    anchor.appendChild(p);
    return p;
  }

  function nativeErrorVisible(input) {
    // Chainlit's own (required) error is a sibling <p class="text-destructive">
    // without our marker class. If it's there, defer to it.
    var anchor = input.parentElement;
    if (
      anchor &&
      anchor.classList &&
      anchor.classList.contains("relative")
    ) {
      anchor = anchor.parentElement || anchor;
    }
    if (!anchor) return false;
    var nodes = anchor.querySelectorAll("p.text-destructive");
    for (var i = 0; i < nodes.length; i++) {
      if (!nodes[i].classList.contains(ERROR_CLASS)) return true;
    }
    return false;
  }

  function applyError(input, message) {
    var node = ensureErrorNode(input);
    if (!node) return;
    if (message && !nativeErrorVisible(input)) {
      node.textContent = message;
      node.style.display = "";
      input.classList.add(INPUT_INVALID_CLASS);
    } else {
      node.textContent = "";
      node.style.display = "none";
      // Only strip the invalid class if Chainlit's own error isn't asking for it.
      if (!nativeErrorVisible(input)) {
        input.classList.remove(INPUT_INVALID_CLASS);
      }
    }
  }

  function attach(input, validator) {
    if (input.dataset.docmindBound === "1") return;
    input.dataset.docmindBound = "1";

    var touched = false;

    function run() {
      applyError(input, validator(input.value));
    }

    input.addEventListener("blur", function () {
      touched = true;
      run();
    });
    input.addEventListener("input", function () {
      if (touched) run();
    });
    // If user submits, reveal validation immediately on next keystroke.
    var form = input.form;
    if (form && !form.dataset.docmindBound) {
      form.dataset.docmindBound = "1";
      form.addEventListener("submit", function () {
        touched = true;
      });
    }
  }

  function scan() {
    var email = document.getElementById("email");
    var password = document.getElementById("password");
    if (email) attach(email, validateUsername);
    if (password) attach(password, validatePassword);
  }

  // The login form mounts/unmounts as the user navigates; watch the DOM.
  function start() {
    scan();
    var observer = new MutationObserver(function () {
      scan();
    });
    observer.observe(document.body, { childList: true, subtree: true });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
  } else {
    start();
  }
})();
