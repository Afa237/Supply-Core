document.addEventListener("DOMContentLoaded", function () {
const sidebar = document.getElementById("sidebar");
const toggle = document.getElementById("sidebarToggle");
const closeButton = document.getElementById("sidebarClose");
const overlay = document.getElementById("sidebarOverlay");


function isMobile() {
    return window.innerWidth <= 992;
}


// ==========================================
// DESKTOP SIDEBAR STATE
// ==========================================

function restoreSidebarState() {

    // Only restore collapsed state on desktop
    if (!isMobile()) {

        const savedState =
            localStorage.getItem("sidebarState");

        if (savedState === "collapsed") {

            sidebar.classList.add("collapsed");

        } else {

            sidebar.classList.remove("collapsed");

        }

    }

}


function saveSidebarState() {

    if (sidebar.classList.contains("collapsed")) {

        localStorage.setItem(
            "sidebarState",
            "collapsed"
        );

    } else {

        localStorage.setItem(
            "sidebarState",
            "expanded"
        );

    }

}


// ==========================================
// MOBILE SIDEBAR
// ==========================================

function openMobileSidebar() {

    sidebar.classList.add("mobile-open");
    overlay.classList.add("active");

}


function closeMobileSidebar() {

    sidebar.classList.remove("mobile-open");
    overlay.classList.remove("active");

}


// ==========================================
// RESTORE SAVED STATE
// ==========================================

restoreSidebarState();


// ==========================================
// SIDEBAR TOGGLE
// ==========================================

toggle.addEventListener("click", function () {

    if (isMobile()) {

        openMobileSidebar();

    } else {

        sidebar.classList.toggle("collapsed");

        // Remember user's desktop choice
        saveSidebarState();

    }

});


// ==========================================
// MOBILE CLOSE BUTTON
// ==========================================

closeButton.addEventListener(
    "click",
    closeMobileSidebar
);


// ==========================================
// MOBILE OVERLAY
// ==========================================

overlay.addEventListener(
    "click",
    closeMobileSidebar
);


// ==========================================
// WINDOW RESIZE
// ==========================================

window.addEventListener("resize", function () {

    if (!isMobile()) {

        closeMobileSidebar();

        // Restore desktop preference
        restoreSidebarState();

    }

});
});