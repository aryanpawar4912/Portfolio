'use strict';

/**
 * Utility Function: Toggles a class on a DOM element
 */
const elementToggleFunc = function (elem) { 
  if (elem) elem.classList.toggle("active"); 
}

/**
 * Responsive Mobile Sidebar Functionality
 */
const sidebar = document.querySelector("[data-sidebar]");
const sidebarBtn = document.querySelector("[data-sidebar-btn]");

if (sidebarBtn && sidebar) {
  sidebarBtn.addEventListener("click", function () { 
    elementToggleFunc(sidebar); 
  });
}

/**
 * Portfolio Filtering Mechanics & Sliding Line Animations
 */
const filterBtn = document.querySelectorAll("[data-filter-btn]");
const filterItems = document.querySelectorAll("[data-filter-item]");
const underlineTracker = document.querySelector(".filter-underline-tracker");

/**
 * High-precision calculation logic for sliding line tracker element
 */
const updateUnderlineTracker = function (activeButton) {
  if (!underlineTracker || !activeButton) return;
  
  // Calculate relative to the nearest parent li container block
  const parentLi = activeButton.parentElement;
  if (!parentLi) return;
  
  const targetLeft = parentLi.offsetLeft;
  const targetWidth = activeButton.offsetWidth;
  
  underlineTracker.style.left = `${targetLeft}px`;
  underlineTracker.style.width = `${targetWidth}px`;
}

/**
 * Core filter processing pipeline
 */
const filterFunc = function (selectedValue) {
  // Normalize comparison values to lowercase clean strings
  const targetValue = selectedValue.toLowerCase().trim();
  
  for (let i = 0; i < filterItems.length; i++) {
    // Read category format safely from dataset attributes
    let itemCategory = filterItems[i].dataset.category ? filterItems[i].dataset.category.toLowerCase().trim() : "";
    
    // Normalize both common space formats and dash slug styles
    itemCategory = itemCategory.replace(/-/g, ' ');

    if (targetValue === "all" || itemCategory.includes(targetValue) || targetValue.includes(itemCategory)) {
      filterItems[i].classList.add("active");
    } else {
      filterItems[i].classList.remove("active");
    }
  }
}

// Bind UI tracking layout triggers
if (filterBtn.length > 0) {
  let lastClickedBtn = document.querySelector("[data-filter-btn].active") || filterBtn[0];
  
  // Initial rendering computations once DOM nodes parse completely
  setTimeout(() => {
    updateUnderlineTracker(lastClickedBtn);
  }, 150);

  window.addEventListener("resize", function() {
    const activeBtn = document.querySelector("[data-filter-btn].active");
    if (activeBtn) updateUnderlineTracker(activeBtn);
  });

  for (let i = 0; i < filterBtn.length; i++) {
    filterBtn[i].addEventListener("click", function () {
      const selectedValue = this.innerText;
      
      filterFunc(selectedValue);
      
      if (lastClickedBtn) {
        lastClickedBtn.classList.remove("active");
      }
      this.classList.add("active");
      lastClickedBtn = this;
      
      updateUnderlineTracker(this);
    });
  }
}

/**
 * Contact Page Interactive Form Validation Pipeline
 */
const form = document.querySelector("[data-form]");
const formInputs = document.querySelectorAll("[data-form-input]");
const formBtn = document.querySelector("[data-form-btn]");

if (form && formInputs.length > 0) {
  for (let i = 0; i < formInputs.length; i++) {
    formInputs[i].addEventListener("input", function () {
      if (form.checkValidity()) {
        if (formBtn) formBtn.removeAttribute("disabled");
      } else {
        if (formBtn) formBtn.setAttribute("disabled", "true");
      }
    });
  }
}