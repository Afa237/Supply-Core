document.addEventListener("DOMContentLoaded", function () {

    const sidebar = document.getElementById("sidebar");
    const toggle = document.getElementById("sidebarToggle");
    const closeButton = document.getElementById("sidebarClose");
    const overlay = document.getElementById("sidebarOverlay");

    function isMobile() {
        return window.innerWidth <= 992;
    }

    function openMobileSidebar() {
        sidebar.classList.add("mobile-open");
        overlay.classList.add("active");
    }

    function closeMobileSidebar() {
        sidebar.classList.remove("mobile-open");
        overlay.classList.remove("active");
    }

    toggle.addEventListener("click", function () {

        if (isMobile()) {
            openMobileSidebar();
        } else {
            sidebar.classList.toggle("collapsed");
        }

    });

    closeButton.addEventListener("click", closeMobileSidebar);
    overlay.addEventListener("click", closeMobileSidebar);

    window.addEventListener("resize", function () {

        if (!isMobile()) {
            closeMobileSidebar();
        }

    });

});