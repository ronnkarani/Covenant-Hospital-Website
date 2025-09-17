// Scroll to Top Button
const scrollBtn = document.getElementById("scrollToTopBtn");

window.onscroll = function () {
  if (document.body.scrollTop > 200 || document.documentElement.scrollTop > 200) {
    scrollBtn.style.display = "block"; // show button
  } else {
    scrollBtn.style.display = "none"; // hide button
  }
};

scrollBtn.addEventListener("click", () => {
  window.scrollTo({
    top: 0,
    behavior: "smooth"
  });
});



// =========================
// Mobile Navbar Toggle
// =========================
const hamburger = document.getElementById('hamburger');
const navLinks = document.getElementById('navLinks');

hamburger.addEventListener('click', () => {
  navLinks.classList.toggle('show');
});

// =========================
// Hero Carousel
// =========================
let slides = document.querySelectorAll('.slide');
let currentIndex = 0;
const slideInterval = 5000; // 5 seconds

function showSlide(index) {
  slides.forEach((slide, i) => {
    slide.classList.remove('active');
    if (i === index) {
      slide.classList.add('active');
    }
  });
}

function nextSlide() {
  currentIndex = (currentIndex + 1) % slides.length;
  showSlide(currentIndex);
}

// Start carousel auto-play
setInterval(nextSlide, slideInterval);

// Initialize first slide
showSlide(currentIndex);

// =========================
// Smooth Scroll for Nav Links
// =========================
const navItems = document.querySelectorAll('.nav-links a');

navItems.forEach(link => {
  link.addEventListener('click', (e) => {
    const href = link.getAttribute('href');

    // Only handle internal section links (skip user dropdown toggle)
    if (href.startsWith('#')) {
      e.preventDefault();
      const targetId = href.substring(1);
      const targetSection = document.getElementById(targetId);

      if (targetSection) {
        targetSection.scrollIntoView({
          behavior: 'smooth'
        });
      }

      // Close nav on mobile after clicking section link
      navLinks.classList.remove('show');
    }
  });
});

// =========================
// User Dropdown Toggle
// =========================
const userDropdown = document.querySelector('.user-dropdown');
const userToggle = document.querySelector('.user-toggle');

if (userToggle && userDropdown) {
  // Toggle dropdown when clicking on the user toggle
  userToggle.addEventListener('click', (e) => {
    e.preventDefault();
    e.stopPropagation(); // prevent closing immediately
    userDropdown.classList.toggle('active');
  });

  // Close dropdown when clicking outside
  document.addEventListener('click', (e) => {
    if (!userDropdown.contains(e.target) && !userToggle.contains(e.target)) {
      userDropdown.classList.remove('active');
    }
  });
}


// static/js/messages.js

document.addEventListener("DOMContentLoaded", function () {
  // Auto-hide alerts after 4 seconds
  setTimeout(() => {
    document.querySelectorAll('.alert').forEach(el => {
      el.style.transition = "opacity 0.5s ease";
      el.style.opacity = "0";
      setTimeout(() => el.remove(), 500);
    });
  }, 4000);
});


// Filter doctors by selected department
  const departmentSelect = document.getElementById('department-select');
  const doctorSelect = document.getElementById('doctor-select');

  departmentSelect.addEventListener('change', function() {
    const dept = this.value;
    Array.from(doctorSelect.options).forEach(option => {
      option.style.display = option.dataset.department === dept || option.value === "" ? "block" : "none";
    });
    doctorSelect.value = "";
  });

/* ======================
     Signup Role → Department Field Toggle
  ====================== */
  const roleSelect = document.querySelector("select[name='user_role']");
  const deptField = document.querySelector(".doctor-field");

  if (roleSelect && deptField) {
    const toggleDept = () => {
      deptField.style.display = roleSelect.value === "doctor" ? "block" : "none";
    };

    roleSelect.addEventListener("change", toggleDept);
    toggleDept(); // run once at load
  }