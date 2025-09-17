document.addEventListener("DOMContentLoaded", () => {
  /* ======================
     Sidebar Toggle
  ====================== */
  const toggleBtn = document.querySelector(".menu-toggle");
  const sidebar = document.querySelector(".dashboard-sidebar");
  const mainContainer = document.querySelector(".dashboard-container");

  if (toggleBtn && sidebar && mainContainer) {
    // Toggle sidebar
    toggleBtn.addEventListener("click", () => {
      sidebar.classList.toggle("active");
      mainContainer.classList.toggle("shifted");
    });

    // Collapse sidebar when clicking outside
    document.addEventListener("click", (e) => {
      if (
        sidebar.classList.contains("active") &&
        !sidebar.contains(e.target) &&
        !toggleBtn.contains(e.target)
      ) {
        sidebar.classList.remove("active");
        mainContainer.classList.remove("shifted");
      }
    });

    // Collapse sidebar on item click
    sidebar.querySelectorAll("li").forEach((item) => {
      item.addEventListener("click", () => {
        sidebar.classList.remove("active");
        mainContainer.classList.remove("shifted");
      });
    });
  }

  /* ======================
     Dropdown Toggle (Navbar)
  ====================== */
  const navRight = document.querySelector(".dashboard-navbar .nav-right");

  if (navRight) {
    navRight.addEventListener("click", (e) => {
      e.stopPropagation(); // prevent immediate close
      navRight.classList.toggle("open");
    });

    // Close dropdown if clicking outside
    document.addEventListener("click", (e) => {
      if (!navRight.contains(e.target)) {
        navRight.classList.remove("open");
      }
    });
  }

  
});
