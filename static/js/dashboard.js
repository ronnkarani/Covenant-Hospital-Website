document.addEventListener("DOMContentLoaded", () => {
  const toggleBtn = document.querySelector(".menu-toggle");
  const sidebar = document.querySelector(".dashboard-sidebar");
  const mainContainer = document.querySelector(".dashboard-container");

  // Toggle sidebar
  toggleBtn.addEventListener("click", () => {
    sidebar.classList.toggle("active");
    mainContainer.classList.toggle("shifted"); // optional push effect
  });

  // Auto collapse when clicking outside
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

  // Auto collapse when clicking on any sidebar item
  sidebar.querySelectorAll("li").forEach((item) => {
    item.addEventListener("click", () => {
      sidebar.classList.remove("active");
      mainContainer.classList.remove("shifted");
    });
  });
});
