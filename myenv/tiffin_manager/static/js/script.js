document.addEventListener("DOMContentLoaded", function () {
    // Keep a Pause form's end_date from being set before its start_date.
    var startInput = document.querySelector('input[name="start_date"]');
    var endInput = document.querySelector('input[name="end_date"]');
    if (startInput && endInput) {
        var sync = function () {
            if (startInput.value) {
                endInput.min = startInput.value;
            }
        };
        startInput.addEventListener("change", sync);
        sync();
    }

    // Confirm before pausing or resuming, since it changes billing.
    document.querySelectorAll("form").forEach(function (form) {
        var submitBtn = form.querySelector('button[type="submit"]');
        if (!submitBtn) return;
        var label = submitBtn.textContent.trim();
        if (label === "Confirm Pause" || label === "Resume delivery") {
            form.addEventListener("submit", function (e) {
                var msg = label === "Confirm Pause"
                    ? "Pause this subscription? Paused days will not be billed."
                    : "Resume delivery starting from the chosen date?";
                if (!window.confirm(msg)) {
                    e.preventDefault();
                }
            });
        }
    });
});
