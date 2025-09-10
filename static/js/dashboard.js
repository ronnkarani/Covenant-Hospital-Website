document.addEventListener("DOMContentLoaded", () => {
  const toggleBtn = document.querySelector(".menu-toggle");
  const sidebar = document.querySelector(".dashboard-sidebar");
  const mainContainer = document.querySelector(".dashboard-container");

  // Sidebar toggle
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

  // =======================
  // Dropdown toggle
  // =======================
  const navRight = document.querySelector(".dashboard-navbar .nav-right");

  if (navRight) {
    navRight.addEventListener("click", (e) => {
      e.stopPropagation(); // don’t close immediately
      navRight.classList.toggle("open");
    });

    // Close dropdown if click outside
    document.addEventListener("click", (e) => {
      if (!navRight.contains(e.target)) {
        navRight.classList.remove("open");
      }
    });
  }
});
