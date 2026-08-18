/**
 * Allied Tours & Travel — shared public/admin UI interactions
 */
(function () {
  "use strict";

  function qs(sel, root) {
    return (root || document).querySelector(sel);
  }
  function qsa(sel, root) {
    return Array.from((root || document).querySelectorAll(sel));
  }

  function toast(message, type) {
    var root = qs("#toast-root");
    if (!root) return;
    var el = document.createElement("div");
    el.className =
      "rounded-md px-4 py-3 text-sm shadow-soft border " +
      (type === "danger"
        ? "bg-red-50 text-red-800 border-red-200"
        : type === "success"
          ? "bg-emerald-50 text-emerald-800 border-emerald-200"
          : "bg-white text-ink border-chocolate/10");
    el.textContent = message;
    root.appendChild(el);
    setTimeout(function () {
      el.remove();
    }, 4000);
  }

  function initMobileMenus() {
    qsa("[data-mobile-toggle]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var targetId = btn.getAttribute("data-mobile-toggle") || btn.getAttribute("aria-controls");
        var panel =
          (targetId && qs("#" + targetId)) ||
          qs("[data-mobile-menu]") ||
          qs("[data-mobile-panel]");
        if (!panel) return;
        var open = panel.classList.toggle("hidden") === false;
        btn.setAttribute("aria-expanded", open ? "true" : "false");
      });
    });
  }

  function initConfirmations() {
    qsa("[data-confirm]").forEach(function (el) {
      el.addEventListener("click", function (e) {
        var msg = el.getAttribute("data-confirm") || "Are you sure?";
        if (!window.confirm(msg)) {
          e.preventDefault();
        }
      });
    });
  }

  function initBookingForm() {
    var form = qs("[data-booking-form]");
    if (!form) return;
    var adults = qs('[name="adults"]', form);
    var children = qs('[name="children"]', form);
    var departure = qs('[name="departure_id"]', form);
    var estimate =
      qs("[data-estimated-total]", form) || qs("[data-booking-estimate]", form);

    function parsePrices() {
      var opt = departure && departure.selectedOptions && departure.selectedOptions[0];
      if (!opt) return { adult: 0, child: 0 };
      var adult = Number(opt.getAttribute("data-price-adult") || 0);
      var child = Number(opt.getAttribute("data-price-child") || 0);
      return { adult: adult, child: child || adult };
    }

    function update() {
      var prices = parsePrices();
      var a = Number((adults && adults.value) || 0);
      var c = Number((children && children.value) || 0);
      var total = a * prices.adult + c * prices.child;
      var currency = form.getAttribute("data-currency") || "KES";
      if (estimate) {
        estimate.textContent = total
          ? currency + " " + total.toLocaleString(undefined, { minimumFractionDigits: 0 })
          : currency + " —";
      }
    }

    [adults, children, departure].forEach(function (el) {
      if (el) el.addEventListener("change", update);
      if (el) el.addEventListener("input", update);
    });
    update();

    var submitting = false;
    form.addEventListener("submit", function (e) {
      if (submitting) {
        e.preventDefault();
        return;
      }
      submitting = true;
      var btn = qs('[type="submit"]', form);
      if (btn) {
        btn.disabled = true;
        btn.textContent = "Submitting…";
      }
    });
  }

  function initGalleryLightbox() {
    var items = qsa("[data-gallery-item]");
    if (!items.length) return;

    var gallery = items.map(function (item) {
      return {
        src: item.getAttribute("href") || item.getAttribute("data-src") || "",
        type: item.getAttribute("data-gallery-type") || "image",
        title: item.getAttribute("data-gallery-title") || "",
        alt: item.getAttribute("data-gallery-alt") || "Gallery media",
      };
    }).filter(function (entry) {
      return !!entry.src;
    });

    if (!gallery.length) return;

    var overlay = null;
    var mediaWrap = null;
    var captionEl = null;
    var counterEl = null;
    var current = 0;
    var activeMedia = null;

    function closeLightbox() {
      if (!overlay) return;
      if (activeMedia && activeMedia.pause) {
        try { activeMedia.pause(); } catch (e) { /* ignore */ }
      }
      document.removeEventListener("keydown", onKey);
      overlay.remove();
      overlay = null;
      activeMedia = null;
      document.body.style.overflow = "";
    }

    function show(index) {
      if (!gallery.length || !mediaWrap) return;
      current = (index + gallery.length) % gallery.length;
      var entry = gallery[current];
      mediaWrap.innerHTML = "";
      activeMedia = null;

      if (entry.type === "video") {
        var video = document.createElement("video");
        video.setAttribute("controls", "");
        video.setAttribute("playsinline", "");
        video.setAttribute("preload", "metadata");
        video.className = "max-h-[78vh] max-w-full rounded-lg object-contain shadow-soft bg-black";
        video.src = entry.src;
        mediaWrap.appendChild(video);
        activeMedia = video;
        video.play().catch(function () { /* autoplay may be blocked */ });
      } else {
        var img = document.createElement("img");
        img.alt = entry.alt;
        img.className = "max-h-[78vh] max-w-full rounded-lg object-contain shadow-soft";
        img.src = entry.src;
        mediaWrap.appendChild(img);
        activeMedia = img;
      }

      if (captionEl) {
        captionEl.textContent = entry.title || "";
        captionEl.classList.toggle("hidden", !entry.title);
      }
      if (counterEl) {
        counterEl.textContent = current + 1 + " / " + gallery.length;
      }
    }

    function onKey(e) {
      if (e.key === "Escape") closeLightbox();
      if (e.key === "ArrowRight") show(current + 1);
      if (e.key === "ArrowLeft") show(current - 1);
    }

    function openLightbox(startIndex) {
      closeLightbox();
      overlay = document.createElement("div");
      overlay.className =
        "fixed inset-0 z-[60] flex items-center justify-center bg-chocolate/92 p-4";
      overlay.setAttribute("role", "dialog");
      overlay.setAttribute("aria-modal", "true");
      overlay.setAttribute("aria-label", "Gallery viewer");
      overlay.innerHTML =
        '<button type="button" data-lightbox-close class="absolute right-4 top-4 z-10 rounded-full bg-cream/10 px-3 py-1 text-2xl leading-none text-white hover:bg-cream/20" aria-label="Close">&times;</button>' +
        '<button type="button" data-lightbox-prev class="absolute left-2 top-1/2 z-10 -translate-y-1/2 rounded-full bg-cream/10 px-3 py-2 text-xl text-white hover:bg-cream/20 md:left-6" aria-label="Previous">‹</button>' +
        '<button type="button" data-lightbox-next class="absolute right-2 top-1/2 z-10 -translate-y-1/2 rounded-full bg-cream/10 px-3 py-2 text-xl text-white hover:bg-cream/20 md:right-6" aria-label="Next">›</button>' +
        '<div class="flex max-h-[90vh] max-w-5xl flex-col items-center gap-3">' +
        '<div data-lightbox-media class="flex max-h-[78vh] max-w-full items-center justify-center"></div>' +
        '<p data-lightbox-caption class="text-center text-sm text-cream/90"></p>' +
        '<p data-lightbox-counter class="text-xs text-cream/60"></p>' +
        '<p class="hidden text-xs text-cream/50 md:block">Use ← → keys to browse · Esc to close</p>' +
        "</div>";

      mediaWrap = overlay.querySelector("[data-lightbox-media]");
      captionEl = overlay.querySelector("[data-lightbox-caption]");
      counterEl = overlay.querySelector("[data-lightbox-counter]");

      overlay.querySelector("[data-lightbox-close]").addEventListener("click", closeLightbox);
      overlay.querySelector("[data-lightbox-prev]").addEventListener("click", function (e) {
        e.stopPropagation();
        show(current - 1);
      });
      overlay.querySelector("[data-lightbox-next]").addEventListener("click", function (e) {
        e.stopPropagation();
        show(current + 1);
      });
      overlay.addEventListener("click", function (e) {
        if (e.target === overlay) closeLightbox();
      });

      document.body.style.overflow = "hidden";
      document.body.appendChild(overlay);
      document.addEventListener("keydown", onKey);
      show(startIndex);
    }

    items.forEach(function (item, index) {
      item.addEventListener("click", function (e) {
        e.preventDefault();
        var raw = item.getAttribute("data-gallery-index");
        var start = raw !== null && raw !== "" ? Number(raw) : index;
        if (Number.isNaN(start)) start = index;
        openLightbox(start);
      });
    });
  }

  function initHeroSlideshow() {
    var root = qs("[data-hero-slideshow]");
    if (!root) return;
    var slides = qsa("[data-hero-slide]", root);
    if (slides.length < 2) return;

    var dots = qsa("[data-hero-dot]", root);
    var intervalMs = Number(root.getAttribute("data-hero-interval") || 6000);
    if (!intervalMs || intervalMs < 2500) intervalMs = 6000;
    var index = 0;
    var timer = null;

    function show(next) {
      index = ((next % slides.length) + slides.length) % slides.length;
      slides.forEach(function (slide, i) {
        slide.classList.toggle("opacity-100", i === index);
        slide.classList.toggle("opacity-0", i !== index);
      });
      dots.forEach(function (dot, i) {
        dot.classList.toggle("bg-gold", i === index);
        dot.classList.toggle("bg-cream/40", i !== index);
      });
    }

    function start() {
      stop();
      timer = window.setInterval(function () {
        show(index + 1);
      }, intervalMs);
    }

    function stop() {
      if (timer) {
        window.clearInterval(timer);
        timer = null;
      }
    }

    dots.forEach(function (dot) {
      dot.addEventListener("click", function () {
        var i = Number(dot.getAttribute("data-hero-index") || 0);
        show(i);
        start();
      });
    });

    root.addEventListener("mouseenter", stop);
    root.addEventListener("mouseleave", start);
    document.addEventListener("visibilitychange", function () {
      if (document.hidden) stop();
      else start();
    });

    show(0);
    start();
  }

  function initCarousel(config) {
    var root = qs(config.root);
    if (!root) return;

    var track = qs(config.track, root);
    var slides = qsa(config.slide, root);
    var dotsWrap = qs(config.dots, root);
    var prevBtn = qs(config.prev);
    var nextBtn = qs(config.next);
    if (!track || slides.length < 2) return;

    var intervalMs = Number(root.getAttribute(config.intervalAttr) || config.defaultInterval || 7000);
    if (!intervalMs || intervalMs < 3000) intervalMs = config.defaultInterval || 7000;

    var index = 0;
    var timer = null;
    var perView = 1;
    var inactiveDot = config.inactiveDot || "bg-cream/35";
    var label = config.label || "page";

    function calcPerView() {
      if (typeof config.perView === "function") return config.perView(slides.length);
      var w = window.innerWidth;
      if (w >= 1024) return Math.min(3, slides.length);
      if (w >= 640) return Math.min(2, slides.length);
      return 1;
    }

    function maxIndex() {
      return Math.max(0, slides.length - perView);
    }

    function renderDots() {
      if (!dotsWrap) return;
      dotsWrap.innerHTML = "";
      var pages = maxIndex() + 1;
      if (pages <= 1) return;
      for (var i = 0; i < pages; i++) {
        var btn = document.createElement("button");
        btn.type = "button";
        btn.className =
          "h-1.5 w-6 rounded-full transition " +
          (i === index ? "bg-gold" : inactiveDot);
        btn.setAttribute("aria-label", "Show " + label + " " + (i + 1));
        btn.setAttribute(config.dotAttr, String(i));
        btn.addEventListener("click", function (e) {
          var target = Number(e.currentTarget.getAttribute(config.dotAttr) || 0);
          goTo(target);
          start();
        });
        dotsWrap.appendChild(btn);
      }
    }

    function goTo(next) {
      var max = maxIndex();
      index = ((next % (max + 1)) + (max + 1)) % (max + 1);
      var slideWidth = slides[0].getBoundingClientRect().width;
      track.style.transform = "translateX(-" + index * slideWidth + "px)";
      if (dotsWrap) {
        qsa("[" + config.dotAttr + "]", dotsWrap).forEach(function (dot, i) {
          dot.classList.toggle("bg-gold", i === index);
          dot.classList.toggle(inactiveDot, i !== index);
        });
      }
    }

    function start() {
      stop();
      if (maxIndex() < 1) return;
      timer = window.setInterval(function () {
        goTo(index + 1);
      }, intervalMs);
    }

    function stop() {
      if (timer) {
        window.clearInterval(timer);
        timer = null;
      }
    }

    function refresh() {
      perView = calcPerView();
      if (index > maxIndex()) index = maxIndex();
      renderDots();
      goTo(index);
    }

    if (prevBtn) {
      prevBtn.addEventListener("click", function () {
        goTo(index - 1);
        start();
      });
    }
    if (nextBtn) {
      nextBtn.addEventListener("click", function () {
        goTo(index + 1);
        start();
      });
    }

    root.addEventListener("mouseenter", stop);
    root.addEventListener("mouseleave", start);
    window.addEventListener("resize", refresh);
    document.addEventListener("visibilitychange", function () {
      if (document.hidden) stop();
      else start();
    });

    refresh();
    start();
  }

  function initTestimonialSlider() {
    initCarousel({
      root: "[data-testimonial-slider]",
      track: "[data-testimonial-track]",
      slide: "[data-testimonial-slide]",
      dots: "[data-testimonial-dots]",
      prev: "[data-testimonial-prev]",
      next: "[data-testimonial-next]",
      intervalAttr: "data-testimonial-interval",
      defaultInterval: 7000,
      dotAttr: "data-testimonial-dot",
      inactiveDot: "bg-chocolate/20",
      label: "testimonials page",
    });
  }

  function initRevealOnScroll() {
    var nodes = qsa("[data-reveal]");
    if (!nodes.length) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      nodes.forEach(function (el) {
        el.classList.add("is-visible");
      });
      return;
    }
    if (!("IntersectionObserver" in window)) {
      nodes.forEach(function (el) {
        el.classList.add("is-visible");
      });
      return;
    }
    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -40px 0px" }
    );
    nodes.forEach(function (el) {
      observer.observe(el);
    });
  }

  function initPartnerMarquee() {
    // Continuous scroll is CSS-driven; sync pause if reduced-motion changes.
    var roots = qsa("[data-partner-marquee]");
    if (!roots.length) return;
    var reduce = window.matchMedia("(prefers-reduced-motion: reduce)");
    function sync() {
      roots.forEach(function (root) {
        var track = qs(".partner-marquee__track", root);
        if (!track) return;
        if (reduce.matches) {
          track.style.animationPlayState = "paused";
        } else {
          track.style.animationPlayState = "";
        }
      });
    }
    sync();
    if (typeof reduce.addEventListener === "function") {
      reduce.addEventListener("change", sync);
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    initMobileMenus();
    initConfirmations();
    initBookingForm();
    initGalleryLightbox();
    initHeroSlideshow();
    initTestimonialSlider();
    initPartnerMarquee();
    initRevealOnScroll();
  });

  window.AlliedUI = { toast: toast };
})();
