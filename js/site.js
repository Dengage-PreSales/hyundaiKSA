/* ============================================================================
   The site layer of the replica: navigation, overlays, the test drive funnel
   and page boot. It replaces the factory template's storefront.js, store.js
   and boot.js in one file, exposing the same surface the ported modules
   consume: window.Storefront { t, openOverlay, closeOverlays, boot } and
   window.Site { cartLines }.

   THE FUNNEL IS THE AUTOMOTIVE MAPPING. On this site "the cart" is the car a
   visitor is arranging to test drive:

     choose a car and version  ->  ec:addToCart
     the details form appears  ->  ec:beginCheckout   (abandon here and the
                                   panel's abandoned basket journey becomes an
                                   abandoned test drive rescue)
     the booking is submitted  ->  ec:order, with the car's real displayed
                                   price and payment_method 'other'

   Every event still flows through js/dengageEvents.js alone; this file only
   decides when to call it.
   ========================================================================== */
(function (window, document) {
    'use strict';

    var $ = function (sel, root) { return (root || document).querySelector(sel); };
    var $$ = function (sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); };

    var slug = window.DEMO_SLUG || 'hyundaiksa';
    var TD_KEY = 'dps:' + slug + ':tdcart';
    var WISH_KEY = 'dps:' + slug + ':wishlist';

    function readJson(key, fallback) {
        try {
            var raw = window.localStorage.getItem(key);
            var parsed = raw ? JSON.parse(raw) : fallback;
            return parsed === null || parsed === undefined ? fallback : parsed;
        } catch (err) { return fallback; }
    }
    function writeJson(key, value) {
        try { window.localStorage.setItem(key, JSON.stringify(value)); } catch (err) { /* private mode */ }
    }

    /* ------------------------------------------------------------------ */
    /* Copy                                                                */

    function t(key, vars) {
        return window.SiteCopy ? window.SiteCopy.t(key, vars) : key;
    }

    /* ------------------------------------------------------------------ */
    /* Overlays: one scrim, drawers and modals toggled with .open           */

    function openOverlay(sel) {
        var el = $(sel);
        if (!el) return;
        closeOverlays();
        el.classList.add('open');
        var scrim = $('#scrim');
        if (scrim) scrim.classList.add('open');
        document.documentElement.classList.add('dps-locked');
    }

    function closeOverlays() {
        $$('.dps-drawer.open, .dps-modal.open').forEach(function (el) { el.classList.remove('open'); });
        var scrim = $('#scrim');
        if (scrim) scrim.classList.remove('open');
        document.documentElement.classList.remove('dps-locked');
    }

    function wireOverlays() {
        document.addEventListener('click', function (event) {
            var opener = event.target.closest ? event.target.closest('[data-open]') : null;
            if (opener) {
                event.preventDefault();
                openOverlay(opener.getAttribute('data-open'));
                return;
            }
            var closer = event.target.closest ? event.target.closest('[data-close]') : null;
            if (closer) { event.preventDefault(); closeOverlays(); return; }
            if (event.target.id === 'scrim') closeOverlays();
        });
        document.addEventListener('keydown', function (event) {
            if (event.key === 'Escape') closeOverlays();
        });
    }

    /* ------------------------------------------------------------------ */
    /* Funnel state                                                        */

    function pending() { return readJson(TD_KEY, null); }
    function setPending(line) {
        if (line) writeJson(TD_KEY, line);
        else { try { window.localStorage.removeItem(TD_KEY); } catch (err) { /* noop */ } }
    }
    function cartLines() {
        var line = pending();
        return line ? [line] : [];
    }

    function wishlist() { return readJson(WISH_KEY, []); }
    function isSaved(id) { return wishlist().indexOf(id) !== -1; }
    function toggleSaved(id) {
        var list = wishlist();
        var at = list.indexOf(id);
        var car = window.Catalog.get(id);
        if (!car) return false;
        if (at === -1) {
            list.push(id);
            window.DengageEvents.addToWishlist({ id: car.id, price: car.price }, 'favorites');
        } else {
            list.splice(at, 1);
            window.DengageEvents.removeFromWishlist({ id: car.id }, 'favorites');
        }
        writeJson(WISH_KEY, list);
        return at === -1;
    }

    function paintHearts() {
        $$('[data-save-car]').forEach(function (el) {
            el.classList.toggle('saved', isSaved(el.getAttribute('data-save-car')));
        });
    }

    /* ------------------------------------------------------------------ */
    /* The test drive modal                                                */

    /* Real trims only where the site displays them; anywhere else the model
       is its own single version, which is a fact rather than a gap. */
    var TRIMS = {
        'tucson':   ['Smart', 'Comfort', 'Premium', 'N Line'],
        'santa-fe': ['GL Smart', 'GL Comfort', 'GL Premium', 'Calligraphy']
    };

    var tdState = { car: null, trim: null, begun: false };

    function tdMarkup(car) {
        var trims = TRIMS[car.id] || [car.name];
        return '' +
            '<div class="dps-modal-head">' +
              '<h2>' + t('testDrive') + '</h2>' +
              '<button type="button" class="dps-x" data-close="1" aria-label="' + t('close') + '">&times;</button>' +
            '</div>' +
            '<div class="dps-modal-body" id="td-body">' +
              '<div class="td-car">' +
                (car.image ? '<img src="' + car.image + '" alt="">' : '') +
                '<div><strong>' + window.Catalog.escapeAttr(car.name) + '</strong>' +
                (car.price ? '<span class="td-price">' + car.price.toLocaleString('en-US') + ' SAR</span>' : '') +
                '</div>' +
              '</div>' +
              '<div class="td-step" id="td-step-trim">' +
                '<h3>' + t('tdChooseTrim') + '</h3>' +
                trims.map(function (trim, i) {
                    return '<label class="td-trim"><input type="radio" name="td-trim" value="' +
                        window.Catalog.escapeAttr(trim) + '"' + (i === 0 ? ' checked' : '') + '> ' +
                        window.Catalog.escapeAttr(trim) + '</label>';
                }).join('') +
                '<button type="button" class="td-btn" id="td-continue">' + t('tdContinue') + '</button>' +
              '</div>' +
              '<div class="td-step" id="td-step-form" hidden>' +
                '<h3>' + t('tdYourDetails') + '</h3>' +
                '<label class="td-field">' + t('tdName') + '<input type="text" id="td-name" autocomplete="name"></label>' +
                '<label class="td-field">' + t('tdMobile') + '<input type="tel" id="td-mobile" dir="ltr" placeholder="+9665xxxxxxxx" autocomplete="tel"></label>' +
                '<label class="td-field">' + t('tdCity') +
                  '<select id="td-city"><option>Jeddah</option><option>Makkah</option><option>Madinah</option><option>Taif</option><option>Tabuk</option><option>Abha</option></select></label>' +
                '<button type="button" class="td-btn" id="td-submit">' + t('tdSubmit') + '</button>' +
              '</div>' +
              '<div class="td-step" id="td-step-done" hidden>' +
                '<p class="td-thanks">' + t('tdThanks') + '</p>' +
              '</div>' +
            '</div>';
    }

    function trimId(car, trim) {
        return car.id + '-' + String(trim).toLowerCase().replace(/[^a-z0-9]+/g, '-');
    }

    function openTestDrive(carId) {
        var car = window.Catalog.get(carId) || window.Catalog.get('tucson');
        if (!car) return;
        var modal = $('#test-drive');
        if (!modal) return;
        tdState = { car: car, trim: null, begun: false };
        modal.innerHTML = tdMarkup(car);
        openOverlay('#test-drive');

        $('#td-continue').addEventListener('click', function () {
            var chosen = modal.querySelector('input[name="td-trim"]:checked');
            tdState.trim = chosen ? chosen.value : null;
            var line = {
                id: car.id,
                variantId: tdState.trim ? trimId(car, tdState.trim) : car.id,
                quantity: 1,
                price: car.price
            };
            setPending(line);
            window.DengageEvents.addToCart(line, cartLines());
            $('#td-step-trim').hidden = true;
            var form = $('#td-step-form');
            form.hidden = false;
            if (!tdState.begun) {
                tdState.begun = true;
                window.DengageEvents.beginCheckout(cartLines());
            }
        });

        $('#td-submit').addEventListener('click', function () {
            var line = pending() || { id: car.id, quantity: 1, price: car.price };
            /* Identify the visitor the same way a capture form does, so the
               booking attaches to a DPS- contact the panel can show. */
            var identity = window.DemoIdentity;
            if (identity && !identity.contactKey && typeof identity.mintKey === 'function') {
                var key = identity.mintKey(Date.now());
                if (window.DengageEvents.setContactKey(key)) {
                    identity.contactKey = key;
                    try { window.sessionStorage.setItem(identity.storageKey, key); } catch (err) { /* noop */ }
                }
            }
            window.DengageEvents.order({
                orderId: 'DPS-' + slug + '-td-' + Date.now(),
                itemCount: 1,
                totalAmount: car.price,
                paymentMethod: 'other'
            }, [line]);
            setPending(null);
            $('#td-step-form').hidden = true;
            $('#td-step-done').hidden = false;
        });
    }

    /* ------------------------------------------------------------------ */
    /* Page furniture the static DOM needs a hand with                      */

    /* The capture carries the site's swiper markup with no swiper runtime.
       Re-animate every carousel the simple way: slides cross-fade in place,
       bullets stay clickable. Layout is untouched, so the capture's own
       swiper CSS keeps doing the positioning. */
    function wireCarousels() {
        $$('.swiper').forEach(function (root) {
            var wrapper = $('.swiper-wrapper', root);
            if (!wrapper) return;
            var slides = $$(':scope > .swiper-slide', wrapper);
            if (slides.length < 2) return;
            /* The capture froze each slide at the capture viewport's width
               (an inline 1440px) with pixel translations to match. On any
               other screen that leaves a bare band beside the hero, so the
               slides are re-based on percentages of their own container. */
            var rtlPage = document.documentElement.dir === 'rtl';
            slides.forEach(function (s, i) {
                s.style.width = '100%';
                s.style.transform = 'translateX(' + (rtlPage ? i * 100 : -i * 100) + '%)';
            });
            var scopeEl = root.closest('section') || root.parentElement || root;
            var dots = $$('.swiper-pagination-bullet', scopeEl);
            var at = 0, timer = null;
            function show(next) {
                at = (next + slides.length) % slides.length;
                slides.forEach(function (s, i) {
                    s.style.opacity = i === at ? '1' : '0';
                    s.style.zIndex = i === at ? '2' : '1';
                    s.style.pointerEvents = i === at ? 'auto' : 'none';
                    s.style.transition = 'opacity .6s ease';
                });
                dots.forEach(function (d, i) {
                    d.classList.toggle('swiper-pagination-bullet-active', i === at);
                });
            }
            function auto() {
                if (timer) window.clearInterval(timer);
                timer = window.setInterval(function () { show(at + 1); }, 6000);
            }
            dots.forEach(function (d, i) {
                d.addEventListener('click', function () { show(i); auto(); });
            });
            /* The arrows and the swipe gesture below both drive the same
               show()/auto() pair, so the crossfade stays the single source
               of slide state. */
            root.__dpsCarousel = {
                next: function () { show(at + 1); auto(); },
                prev: function () { show(at - 1); auto(); }
            };
            var swipe = null;
            root.addEventListener('pointerdown', function (e) { swipe = e.clientX; });
            root.addEventListener('pointerup', function (e) {
                if (swipe === null) return;
                var dx = e.clientX - swipe;
                swipe = null;
                if (Math.abs(dx) < 40) return;
                var rtl = document.documentElement.dir === 'rtl';
                var forward = rtl ? dx > 0 : dx < 0;
                if (forward) { show(at + 1); } else { show(at - 1); }
                auto();
            });
            show(0); auto();
        });
    }

    /* ------------------------------------------------------------------ */
    /* The rest of the scripted site furniture. The live property drives
       its card rails with GSAP Draggable, its dropdowns with react-select
       and its showroom pane with Google Maps; none of that script survives
       a static capture, so the same affordances are rebuilt here.          */

    function wireDragRails() {
        $$('.feacted_model_list').forEach(function (rail) {
            var box = rail.parentElement;
            if (!box || box.__dpsRail) return;
            box.__dpsRail = true;
            box.classList.add('dps-rail');
            box.style.overflowX = 'auto';
            var drag = null;
            box.addEventListener('pointerdown', function (e) {
                drag = { x: e.clientX, left: box.scrollLeft, moved: 0 };
            });
            window.addEventListener('pointermove', function (e) {
                if (!drag) return;
                var dx = e.clientX - drag.x;
                drag.moved = Math.max(drag.moved, Math.abs(dx));
                if (drag.moved > 4) box.scrollLeft = drag.left - dx;
            });
            window.addEventListener('pointerup', function () {
                if (drag && drag.moved > 6) box.__dpsSquelch = Date.now();
                drag = null;
            });
            /* A drag must not fire the card click it ends on. */
            box.addEventListener('click', function (e) {
                if (box.__dpsSquelch && Date.now() - box.__dpsSquelch < 250) {
                    e.preventDefault();
                    e.stopPropagation();
                }
            }, true);
            /* The section's dots become coarse scroll positions. */
            var sec = box.closest('section') || box.parentElement;
            var pag = sec && sec.querySelector('[class*="pagination"]');
            if (pag) {
                var dots = $$(':scope > *', pag);
                dots.forEach(function (d, i) {
                    d.style.cursor = 'pointer';
                    d.addEventListener('click', function () {
                        var max = box.scrollWidth - box.clientWidth;
                        box.scrollTo({ left: max * (dots.length > 1 ? i / (dots.length - 1) : 0), behavior: 'smooth' });
                    });
                });
            }
        });
    }

    function wireArrows() {
        $$('button[aria-label="Previous slide"], button[aria-label="Next slide"]').forEach(function (btn) {
            if (btn.__dpsArrow) return;
            btn.__dpsArrow = true;
            var forward = btn.getAttribute('aria-label') === 'Next slide';
            btn.addEventListener('click', function (e) {
                e.preventDefault();
                var node = btn.parentElement;
                while (node && node !== document.body) {
                    var sw = node.querySelector && node.querySelector('.swiper');
                    if (sw && sw.__dpsCarousel) {
                        if (forward) { sw.__dpsCarousel.next(); } else { sw.__dpsCarousel.prev(); }
                        return;
                    }
                    var rail = node.querySelector && node.querySelector('.dps-rail');
                    if (rail && rail.scrollWidth > rail.clientWidth + 8) {
                        var rtl = document.documentElement.dir === 'rtl';
                        var step = Math.max(280, Math.round(rail.clientWidth * 0.7));
                        rail.scrollBy({ left: step * (forward ? 1 : -1) * (rtl ? -1 : 1), behavior: 'smooth' });
                        return;
                    }
                    node = node.parentElement;
                }
            });
        });
    }

    /* react-select renders its menu only while open, so a capture holds an
       empty shell. Each shell gets a plain menu whose options come from the
       page itself where possible (the branch names on it), and from the
       catalogue and the region the site serves otherwise. */
    function selectOptionsFor(label, ar, branches) {
        var l = label.toLowerCase();
        if (/branch|dealer|فرع/.test(l)) return branches;
        if (/service type|نوع الخدمة/.test(l)) {
            return ar ? ['صيانة دورية', 'إصلاح وتشخيص', 'هيكل ودهان']
                      : ['Periodic Maintenance', 'Repair & Diagnostics', 'Body & Paint'];
        }
        if (/type|النوع/.test(l)) {
            return ar ? ['معرض', 'مركز خدمة', 'قطع غيار']
                      : ['Showroom', 'Service Center', 'Spare Parts'];
        }
        if (/city|مدينة/.test(l)) {
            return ar ? ['جدة', 'مكة المكرمة', 'المدينة المنورة', 'الطائف', 'تبوك', 'ينبع']
                      : ['Jeddah', 'Makkah', 'Madinah', 'Taif', 'Tabuk', 'Yanbu'];
        }
        if (/vehicle|model|سيارة|مركبة|موديل|طراز/.test(l)) {
            return window.Catalog ? window.Catalog.all().map(function (c) { return c.name; }) : null;
        }
        if (/year|سنة/.test(l)) return ['2026', '2025', '2024', '2023', '2022', '2021', '2020'];
        if (/gender|الجنس/.test(l)) return ar ? ['ذكر', 'أنثى'] : ['Male', 'Female'];
        if (/inquiry|استفسار/.test(l)) {
            return ar ? ['استفسار مبيعات', 'استفسار صيانة', 'شكوى', 'أخرى']
                      : ['Sales inquiry', 'Service inquiry', 'Complaint', 'Other'];
        }
        if (/mileage|المسافة/.test(l)) {
            return ar ? ['أقل من 10,000 كم', '10,000–50,000 كم', '50,000–100,000 كم', 'أكثر من 100,000 كم']
                      : ['Under 10,000 km', '10,000–50,000 km', '50,000–100,000 km', 'Over 100,000 km'];
        }
        return null;
    }

    function pageBranches(ar) {
        var found = [];
        $$('.showroom_header_text').forEach(function (h) {
            var name = h.textContent.trim();
            if (name && found.indexOf(name) === -1) found.push(name);
        });
        if (found.length) return found;
        return ar ? ['معرض طريق الحرمين', 'معرض أوتو مول', 'معرض طريق الملك عبدالله', 'معرض طريق المدينة', 'معرض أبحر']
                  : ['Al-Haramain Road Showroom', 'Auto Mall Showroom', 'King Abdullah Road Showroom', 'Madinah Road Showroom', 'Obhur Showroom'];
    }

    function setMapName(name) {
        $$('.dps-map-name').forEach(function (el) { el.textContent = name; });
    }

    function wireSelects() {
        var ar = langCode() === 'ar';
        var branches = pageBranches(ar);
        $$('.input_group_select').forEach(function (sel) {
            if (sel.__dpsSel) return;
            sel.__dpsSel = true;
            var group = sel.closest('.input_group') || sel.parentElement;
            var labelEl = group && group.querySelector('.input_group_label');
            var label = labelEl ? labelEl.textContent.trim() : '';
            var opts = selectOptionsFor(label, ar, branches);
            if (!opts || !opts.length) return;
            var menu = document.createElement('div');
            menu.className = 'dps-select-menu';
            menu.hidden = true;
            opts.forEach(function (o) {
                var b = document.createElement('button');
                b.type = 'button';
                b.className = 'dps-select-opt';
                b.textContent = o;
                b.addEventListener('click', function (e) {
                    e.stopPropagation();
                    var face = sel.querySelector('[class*="placeholder"]') ||
                               sel.querySelector('[class*="singleValue"]');
                    if (face) face.textContent = o;
                    sel.setAttribute('data-dps-value', o);
                    menu.hidden = true;
                    if (/branch|فرع/i.test(label)) {
                        var card = $$('.showroom_header_text').filter(function (h) {
                            return h.textContent.trim() === o;
                        })[0];
                        if (card) card.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        setMapName(o);
                    }
                });
                menu.appendChild(b);
            });
            sel.style.position = 'relative';
            sel.appendChild(menu);
            sel.addEventListener('click', function (e) {
                e.stopPropagation();
                var willOpen = menu.hidden;
                $$('.dps-select-menu').forEach(function (m) { m.hidden = true; });
                menu.hidden = !willOpen;
            });
        });
        document.addEventListener('click', function () {
            $$('.dps-select-menu').forEach(function (m) { m.hidden = true; });
        });
    }

    /* Two-button choice rows (preferred call time and friends): the first
       option ships styled active; clicking makes the choice real. */
    function wireChoiceChips() {
        $$('.input_group').forEach(function (group) {
            if (group.__dpsChips || group.querySelector('.input_group_select')) return;
            var chips = $$(':scope > div > button, :scope > button', group).filter(function (b) {
                return b.type !== 'submit' && b.textContent.trim().length > 2;
            });
            if (chips.length < 2) return;
            group.__dpsChips = true;
            chips.forEach(function (chip) {
                chip.addEventListener('click', function (e) {
                    e.preventDefault();
                    chips.forEach(function (c) {
                        var on = c === chip;
                        c.style.background = on ? '#002c5f' : '#ffffff';
                        c.style.color = on ? '#ffffff' : '#0e1215';
                        c.style.borderColor = on ? '#002c5f' : '#ebebeb';
                    });
                });
            });
        });
    }

    /* The showroom pane hosts a Google Map on the live property. A quiet
       map-styled card holds the ground here, and Get Directions opens the
       real map in a new tab, which is what the control promises. */
    function wireShowroomMap() {
        $$('.showroom_map').forEach(function (map) {
            if (map.__dpsMap) return;
            map.__dpsMap = true;
            map.style.position = 'relative';
            var ph = document.createElement('div');
            ph.className = 'dps-map';
            ph.innerHTML =
                '<svg viewBox="0 0 24 24" class="dps-map-pin" aria-hidden="true">' +
                '<path fill="#002c5f" d="M12 2a7 7 0 0 0-7 7c0 5 7 13 7 13s7-8 7-13a7 7 0 0 0-7-7zm0 9.5A2.5 2.5 0 1 1 12 6a2.5 2.5 0 0 1 0 5.5z"/></svg>' +
                '<span class="dps-map-name"></span>';
            map.appendChild(ph);
            var first = $('.showroom_header_text');
            if (first) setMapName(first.textContent.trim());
        });

        document.addEventListener('click', function (event) {
            var btn = event.target.closest ? event.target.closest('button, a') : null;
            if (!btn) return;
            if (!/get directions|الاتجاهات/i.test(btn.textContent)) return;
            event.preventDefault();
            var node = btn, header = null;
            while (node && node !== document.body && !header) {
                header = node.querySelector ? node.querySelector('.showroom_header_text') : null;
                node = node.parentElement;
            }
            var name = header ? header.textContent.trim() : 'Mohamed Yousuf Naghi Motors Hyundai';
            setMapName(name);
            window.open('https://www.google.com/maps/search/?api=1&query=' +
                encodeURIComponent(name + ' Hyundai Jeddah'), '_blank', 'noopener');
        });

        /* A branch card click focuses that branch: the map card names it and
           comes into view. The card's chevron rides the same behaviour. */
        document.addEventListener('click', function (event) {
            var head = event.target.closest ? event.target.closest('.showroom_header_text') : null;
            if (!head) {
                var row = event.target.closest ? event.target.closest('[class*="showroom"]') : null;
                head = row && row.querySelector ? row.querySelector('.showroom_header_text') : null;
            }
            if (!head) return;
            setMapName(head.textContent.trim());
            var map = $('.showroom_map');
            if (map) map.scrollIntoView({ behavior: 'smooth', block: 'center' });
        });
    }

    /* ------------------------------------------------------------------ */
    /* The demonstration-site contract: everything visible is real. Every
       control below either performs its action here, or opens the SAME
       content on the live property in a new tab. Nothing on screen is a
       dead placeholder.                                                   */

    function liveSite(pathname) {
        window.open('https://hyundaiksa.com' + pathname, '_blank', 'noopener');
    }

    function twinLanguageUrl() {
        if (document.body.hasAttribute('data-gateway')) {
            var pre = sitePrefix();
            return langCode() === 'ar' ? pre + 'en/index.html' : pre + 'index.html';
        }
        var p = location.pathname;
        if (p.indexOf('/en/') !== -1) return p.replace('/en/', '/ar/');
        if (p.indexOf('/ar/') !== -1) return p.replace('/ar/', '/en/');
        return p;
    }

    var lightSet = [], lightAt = 0;
    function stepLightbox(d) {
        if (!lightSet.length) return;
        lightAt = (lightAt + d + lightSet.length) % lightSet.length;
        var lb = $('#dps-lightbox');
        if (lb) lb.querySelector('img').src = lightSet[lightAt];
    }
    function openLightbox(set, at) {
        if (!set.length) return;
        lightSet = set;
        lightAt = Math.max(0, at);
        var lb = $('#dps-lightbox');
        if (!lb) {
            lb = document.createElement('div');
            lb.id = 'dps-lightbox';
            lb.innerHTML = '<button type="button" class="lb-x" aria-label="Close">&times;</button>' +
                '<button type="button" class="lb-prev" aria-label="Previous">&#8249;</button>' +
                '<img alt="">' +
                '<button type="button" class="lb-next" aria-label="Next">&#8250;</button>';
            document.body.appendChild(lb);
            lb.addEventListener('click', function (e) {
                if (e.target === lb || e.target.classList.contains('lb-x')) lb.classList.remove('open');
                else if (e.target.classList.contains('lb-prev')) stepLightbox(-1);
                else if (e.target.classList.contains('lb-next')) stepLightbox(1);
            });
            document.addEventListener('keydown', function (e) {
                if (!lb.classList.contains('open')) return;
                if (e.key === 'Escape') lb.classList.remove('open');
                if (e.key === 'ArrowRight') stepLightbox(1);
                if (e.key === 'ArrowLeft') stepLightbox(-1);
            });
        }
        stepLightbox(0);
        lb.classList.add('open');
    }
    function sectionImages(el) {
        var scope = el.closest('section') || el.closest('main') || document;
        var seen = [];
        $$('img', scope).forEach(function (i) {
            var s = i.currentSrc || i.src;
            if (s && i.naturalWidth > 40 && seen.indexOf(s) === -1) seen.push(s);
        });
        return seen;
    }

    function wireUniversalCtas() {
        var lang = langCode();
        var pre = sitePrefix();
        var tenant = pre + lang + '/mynaghi/';
        var isHome = document.body.getAttribute('data-page-type') === 'home';

        /* Language switcher is a button on this build. */
        $$('.lang_switcher').forEach(function (el) {
            if (el.__dps) return; el.__dps = true; if (el.setAttribute) el.setAttribute('data-dps-wired', '1');
            el.addEventListener('click', function () { location.href = twinLanguageUrl(); });
        });

        /* Login opens the property's real sign-in. */
        $$('.profile_button').forEach(function (el) {
            if (el.__dps) return; el.__dps = true; if (el.setAttribute) el.setAttribute('data-dps-wired', '1');
            el.removeAttribute('data-demo-dead');
            el.addEventListener('click', function (e) {
                e.preventDefault();
                liveSite('/' + lang + '/mynaghi/login');
            });
        });

        /* A hero slide's Explore goes to that slide's own model page. */
        $$('.swiper-slide').forEach(function (slide) {
            var btn = slide.querySelector('button[aria-label="Explore"], button[aria-label="اكتشف"], button[aria-label="استكشف"]');
            if (!btn || btn.__dps) return;
            btn.__dps = true; if (btn.setAttribute) btn.setAttribute('data-dps-wired', '1');
            btn.addEventListener('click', function () {
                var txt = (slide.textContent || '').toUpperCase();
                var model = null;
                window.Catalog.all().forEach(function (c) {
                    if (!model && (txt.indexOf(c.nameEn.toUpperCase()) !== -1 || txt.indexOf(c.nameAr) !== -1)) model = c;
                });
                if (model) { location.href = tenant + 'models/' + model.path + '/index.html'; return; }
                var grid = $('#dn_inline_target_in_grid');
                if (grid) grid.scrollIntoView({ behavior: 'smooth', block: 'center' });
                else location.href = tenant + 'index.html';
            });
        });

        /* The services cards on the home page. */
        if (isHome) {
            [['Call Center', 'مركز الاتصال', function () { location.href = 'tel:8001240191'; }],
             ['After Sales Network', 'شبكة ما بعد البيع', function () { location.href = tenant + 'service-booking/index.html'; }],
             ['Service Booking', 'حجز الصيانة', function () { location.href = tenant + 'service-booking/index.html'; }]
            ].forEach(function (row) {
                $$('h1,h2,h3,h4,h5,p').forEach(function (h) {
                    var t2 = h.textContent.trim();
                    if (t2 !== row[0] && t2 !== row[1]) return;
                    var card = h.closest('div');
                    for (var k = 0; k < 2 && card && !card.querySelector('img,svg'); k++) card = card.parentElement;
                    if (!card || card.__dps) return;
                    card.__dps = true; if (card.setAttribute) card.setAttribute('data-dps-wired', '1');
                    card.style.cursor = 'pointer';
                    card.addEventListener('click', row[2]);
                });
            });
        }

        /* Trim comparison scrolls to the trims block. */
        function trimsBlock() {
            var head = $$('h1,h2,h3,h4').filter(function (h) {
                return /trim|الفئة|فئة/i.test(h.textContent);
            })[0];
            return head || $('#dn_inline_target_pdp_below_price');
        }

        /* Text-routed CTAs: prefer the nearest real link in the same card,
           fall back to the closest sensible page. */
        function nearestHref(el) {
            var n = el, hops = 0;
            while (n && n !== document.body && hops < 4) {
                if (n.tagName === 'A' && n.getAttribute('href') && n.getAttribute('href') !== '#') return n;
                var a2 = n.querySelector && n.querySelector('a[href]:not([href^="#"])');
                if (a2 && a2 !== el) return a2;
                n = n.parentElement; hops++;
            }
            return null;
        }
        var CTA = [
            [/^(learn more|know more|اعرف المزيد|تعرف على المزيد)$/i, function (b) {
                var a = nearestHref(b);
                if (a) { a.click(); return; }
                location.href = tenant + 'service-booking/index.html';
            }],
            [/^(view details|offer details|تفاصيل العرض|عرض التفاصيل)$/i, function (b) {
                var a = nearestHref(b);
                if (a) { a.click(); return; }
                location.href = tenant + 'offers/index.html';
            }],
            [/^(read more|اقرأ المزيد)$/i, function (b) {
                var a = nearestHref(b);
                if (a) { a.click(); return; }
                liveSite('/' + lang + '/mynaghi');
            }],
            [/^(e-brochure|كتيب إلكتروني)$/i, function () {
                liveSite('/' + lang + '/mynaghi/offers/backtoschool');
            }],
            [/^(explore more|أكتشف أكثر|اكتشف أكثر)$/i, function () {
                var grid = $('#dn_inline_target_in_grid');
                if (grid) grid.scrollIntoView({ behavior: 'smooth', block: 'center' });
                else location.href = tenant + 'index.html';
            }],
            [/^(compare trims|مقارنة العناصر|trim details|تفاصيل الفئة)$/i, function () {
                var t3 = trimsBlock();
                if (t3) t3.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }]
        ];
        $$('main button, main [role="button"]').forEach(function (b) {
            if (b.__dps) return;
            var t2 = b.textContent.trim();
            var aria = (b.getAttribute('aria-label') || '').trim();
            for (var i = 0; i < CTA.length; i++) {
                if (CTA[i][0].test(t2) || CTA[i][0].test(aria)) {
                    b.__dps = true; if (b.setAttribute) b.setAttribute('data-dps-wired', '1');
                    var act = CTA[i][1];
                    b.addEventListener('click', function (e) { e.preventDefault(); act(b); });
                    break;
                }
            }
        });

        /* The exterior/interior switch: the interior media set is mounted on
           demand on the live property and is not in a static capture, so the
           section keeps a single plain heading instead of a broken toggle. */
        $$('button').forEach(function (b) {
            var t2 = b.textContent.trim();
            if (/^(Interior|التصميم الداخلي)$/.test(t2)) b.style.display = 'none';
            if (/^(Exterior|التصميم الخارجي)$/.test(t2)) {
                b.style.pointerEvents = 'none';
                b.setAttribute('tabindex', '-1');
            }
        });

        /* Campaign detail folds (Terms, Disclaimer): open their own block. */
        $$('main button').forEach(function (b) {
            var t2 = b.textContent.trim();
            if (!/^(Terms & Conditions|Disclaimer|الشروط والأحكام|التوضيح|إخلاء المسؤولية)$/.test(t2) || b.__dps) return;
            var box = (b.parentElement && b.parentElement.nextElementSibling) || b.nextElementSibling;
            if (!box || !box.textContent.trim()) { b.style.display = 'none'; return; }
            b.__dps = true; if (b.setAttribute) b.setAttribute('data-dps-wired', '1');
            if (box.clientHeight > 4) { box.style.overflow = 'hidden'; box.style.height = '0px'; }
            b.addEventListener('click', function () {
                var open = box.clientHeight > 4;
                box.style.transition = 'height .25s ease';
                box.style.overflow = 'hidden';
                box.style.height = open ? '0px' : box.scrollHeight + 'px';
            });
        });
    }

    function wireGallery() {
        document.addEventListener('click', function (e) {
            var b = e.target.closest ? e.target.closest('button') : null;
            if (!b) return;
            var aria = b.getAttribute('aria-label') || '';
            if (/gallery image|صورة المعرض/i.test(aria) ||
                (b.querySelector('img') && /flex-shrink-0/.test(b.className) && b.closest('[class*="allery"]'))) {
                var img = b.querySelector('img');
                var set = sectionImages(b);
                openLightbox(set, Math.max(0, set.indexOf(img ? (img.currentSrc || img.src) : '')));
                return;
            }
            if (/fullscreen|ملء الشاشة/i.test(aria) || /fullscreen_btn/.test(b.className)) {
                var scope = b.closest('section') || document;
                var vis = $$('.swiper-slide', scope).filter(function (s) { return s.style.opacity !== '0'; })[0];
                var im = vis && vis.querySelector('img');
                var set2 = sectionImages(b);
                openLightbox(set2, Math.max(0, set2.indexOf(im ? (im.currentSrc || im.src) : '')));
                return;
            }
            if (/^(Next|Previous) Image$/i.test(aria) || /الصورة (التالية|السابقة)/.test(aria)) {
                var dir = /Next|التالية/.test(aria) ? 1 : -1;
                var lb = $('#dps-lightbox');
                if (lb && lb.classList.contains('open')) { stepLightbox(dir); return; }
                var sec = b.closest('section') || document;
                var sw = sec.querySelector('.swiper');
                if (sw && sw.__dpsCarousel) {
                    if (dir === 1) { sw.__dpsCarousel.next(); } else { sw.__dpsCarousel.prev(); }
                    return;
                }
                var rail = sec.querySelector('.dps-rail, [class*="overflow-x"]');
                if (rail) rail.scrollBy({ left: dir * 320, behavior: 'smooth' });
            }
        });
    }

    function wireAccordions() {
        document.addEventListener('click', function (event) {
            var head = event.target.closest ? event.target.closest('[data-hy-acc]') : null;
            if (!head) return;
            var body = head.nextElementSibling;
            if (!body) return;
            var openNow = body.style.height !== '0px' && body.style.height !== '';
            body.style.height = openNow ? '0px' : 'auto';
            body.style.opacity = openNow ? '0' : '1';
            head.classList.toggle('open', !openNow);
        });
    }

    function wireTabs() {
        $$('[data-hy-tabs]').forEach(function (root) {
            var tabs = $$('[data-hy-tab]', root);
            var panes = $$('[data-hy-pane]', root);
            tabs.forEach(function (tab, i) {
                tab.addEventListener('click', function () {
                    tabs.forEach(function (x, j) { x.classList.toggle('active', j === i); });
                    panes.forEach(function (p, j) { p.hidden = j !== i; });
                });
            });
        });
    }

    function wireCountdowns() {
        $$('[data-countdown-to]').forEach(function (el) {
            var target = new Date(el.getAttribute('data-countdown-to')).getTime();
            if (!isFinite(target)) return;
            var fields = {
                d: $('[data-cd-d]', el), h: $('[data-cd-h]', el),
                m: $('[data-cd-m]', el), s: $('[data-cd-s]', el)
            };
            function tick() {
                var left = Math.max(0, target - Date.now());
                var d = Math.floor(left / 86400000);
                var h = Math.floor(left / 3600000) % 24;
                var m = Math.floor(left / 60000) % 60;
                var s = Math.floor(left / 1000) % 60;
                if (fields.d) fields.d.textContent = String(d).padStart(2, '0');
                if (fields.h) fields.h.textContent = String(h).padStart(2, '0');
                if (fields.m) fields.m.textContent = String(m).padStart(2, '0');
                if (fields.s) fields.s.textContent = String(s).padStart(2, '0');
            }
            tick();
            window.setInterval(tick, 1000);
        });
    }

    function toast(message) {
        var note = $('#dps-toast');
        if (!note) {
            note = document.createElement('div');
            note.id = 'dps-toast';
            document.body.appendChild(note);
        }
        note.textContent = message;
        note.classList.add('show');
        window.setTimeout(function () { note.classList.remove('show'); }, 2400);
    }

    /* Links the replica does not cover open a small notice instead of a 404
       or, worse, the live site mid demo. */
    function wireDeadLinks() {
        document.addEventListener('click', function (event) {
            var dead = event.target.closest ? event.target.closest('[data-demo-dead]') : null;
            if (!dead) return;
            event.preventDefault();
            toast(t('notPart'));
        });
    }

    /* The lead forms post to the live property's backend, which this replica
       does not carry (its README says so). Submitting one instead does what
       the story needs: the visitor becomes an identified DPS- contact. The
       footer newsletter hands over to the shared capture campaign, whose
       popup writes the contact, with consent, the native way. Inquire Now is
       a lead-form modal on the live site; the contact page is this replica's
       inquiry desk. */
    function wireLeadForms() {
        var ar = langCode() === 'ar';
        var thanks = ar ? 'شكراً لك — أصبحت الآن جهة اتصال معرّفة في هذا العرض.'
                        : 'Thank you — you are now an identified contact in this demo.';

        function mintIdentity() {
            var identity = window.DemoIdentity;
            if (identity && !identity.contactKey && typeof identity.mintKey === 'function') {
                var key = identity.mintKey(Date.now());
                if (window.DengageEvents.setContactKey(key)) {
                    identity.contactKey = key;
                    try { window.sessionStorage.setItem(identity.storageKey, key); } catch (err) { /* noop */ }
                }
            }
        }

        document.addEventListener('submit', function (event) {
            var form = event.target;
            if (!form || form.tagName !== 'FORM') return;
            if (form.closest('#dengage-panel, #test-drive, #inbox, #site-menu')) return;
            event.preventDefault();
            if (form.closest('footer')) {
                window.DengageEvents.scenario('subscription-popup');
                return;
            }
            mintIdentity();
            toast(thanks);
        });

        var pre = sitePrefix();
        var lang = langCode();
        var inquiryLabels = ['Inquire Now', 'Buy Now', 'Order Now',
                             'اطلبه الآن', 'اشتره الآن', 'اشترِ الآن', 'استفسر الآن'];
        $$('main button').forEach(function (btn) {
            var name = (btn.getAttribute('aria-label') || btn.textContent || '').trim();
            if (inquiryLabels.indexOf(name) === -1) return;
            btn.addEventListener('click', function () {
                location.href = pre + lang + '/mynaghi/contact-us/index.html';
            });
        });
    }

    /* The footer's link columns arrive collapsed (a scripted reveal with no
       move- class, so the build's settle pass never saw them). Open every
       collapsed block that actually holds content; the demo layer's own
       closed menus stay closed. */
    function dressFooter() {
        $$('footer *').forEach(function (el) {
            if (el.className && /dps-/.test(el.className.toString())) return;
            var cs = getComputedStyle(el);
            if (cs.display === 'none') return;
            if (parseFloat(cs.opacity) === 0 || el.clientHeight === 0 ||
                cs.visibility === 'hidden' || cs.transform !== 'none') {
                if (el.clientHeight === 0 && el.textContent.trim()) {
                    el.style.height = 'auto';
                    el.style.maxHeight = 'none';
                }
                el.style.opacity = '1';
                el.style.transform = 'none';
                el.style.visibility = 'visible';
            }
        });
    }

    /* The service-booking page pairs its form with an illustration the live
       site mounts by script; the left column otherwise sits empty. The
       page gets the property's own service-booking photograph. */
    function dressServicePage() {
        if (location.pathname.indexOf('service-booking') === -1) return;
        var heads = $$('main h1, main h2').filter(function (h) { return h.textContent.trim().length > 4; });
        var head = heads[0];
        if (!head) return;
        var col = head.parentElement;
        if (!col || col.querySelector('img')) return;
        var img = document.createElement('img');
        img.src = sitePrefix() + 'assets/img/cdn/cmssection/23079/service-booking.webp';
        img.alt = '';
        img.style.cssText = 'width:560px;max-width:92%;height:auto;border-radius:8px;margin-top:28px;display:block;';
        col.appendChild(img);
    }

    /* The colour configurator is fed by an API call the live site makes when
       a colour is picked; its car renders are simply not in a static capture,
       and a stage with no car on it reads as a fault. The section rests. */
    function hideColorConfigurators() {
        $$('.model-color-wrapper').forEach(function (w) {
            var sec = w.closest('section') || w.parentElement.parentElement;
            if (sec) sec.style.display = 'none';
        });
    }

    function wireFunnelButtons() {
        document.addEventListener('click', function (event) {
            var book = event.target.closest ? event.target.closest('[data-book-test-drive]') : null;
            if (book) {
                event.preventDefault();
                openTestDrive(book.getAttribute('data-book-test-drive') ||
                    document.body.getAttribute('data-product-id') || 'tucson');
                return;
            }
            var heart = event.target.closest ? event.target.closest('[data-save-car]') : null;
            if (heart) {
                event.preventDefault();
                toggleSaved(heart.getAttribute('data-save-car'));
                paintHearts();
            }
        });
    }

    /* ------------------------------------------------------------------ */
    /* Header. The live site drives all of this with script: dropdowns are
       height-animated wrappers, the white "force-hovered" dress arrives on
       hover and on scroll, and the burger mounts a full-screen menu that a
       static capture never contains. The same affordances are rebuilt here,
       with the replica's own site map behind the burger.                    */

    function langCode() {
        return (document.documentElement.getAttribute('lang') || 'en').indexOf('ar') === 0 ? 'ar' : 'en';
    }

    function sitePrefix() {
        var m = location.pathname.match(/^(.*?)\/(en|ar)\//);
        if (m) return m[1] + '/';
        return location.pathname.replace(/[^/]*$/, '');
    }

    function buildSiteMenu() {
        if ($('#site-menu') || !window.Catalog) return;
        var ar = langCode() === 'ar';
        var pre = sitePrefix();
        var lang = langCode();
        function page(rest) { return pre + lang + '/mynaghi/' + rest; }
        var groups = [
            { title: ar ? 'سيدان' : 'Sedan', cat: 'Sedan' },
            { title: ar ? 'الدفع الرباعي' : 'SUV', cat: 'SUV' },
            { title: ar ? 'العائلية' : 'MPV', cat: 'MPV' }
        ];
        var rows = groups.map(function (g) {
            var cars = window.Catalog.all().filter(function (c) { return c.category === g.cat; });
            return '<div class="dps-menu-group"><h3>' + g.title + '</h3>' +
                cars.map(function (c) {
                    return '<a class="dps-menu-link" href="' + page('models/' + c.path + '/index.html') + '">' +
                        window.Catalog.escapeAttr(c.name) + '</a>';
                }).join('') + '</div>';
        }).join('');
        var links = '<div class="dps-menu-group"><h3>' + (ar ? 'تصفح' : 'Browse') + '</h3>' +
            '<a class="dps-menu-link" href="' + page('index.html') + '">' + (ar ? 'الرئيسية' : 'Home') + '</a>' +
            '<a class="dps-menu-link" href="' + page('offers/index.html') + '">' + (ar ? 'العروض' : 'Offers') + '</a>' +
            '<a class="dps-menu-link" href="' + page('offers/back-to-school/index.html') + '">' + (ar ? 'عرض العودة للمدارس' : 'Back to School offer') + '</a>' +
            '<a class="dps-menu-link" href="' + page('service-booking/index.html') + '">' + (ar ? 'حجز الصيانة' : 'Service booking') + '</a>' +
            '<a class="dps-menu-link" href="' + page('contact-us/index.html') + '">' + (ar ? 'اتصل بنا' : 'Contact us') + '</a>' +
            '<a class="dps-menu-link" href="' + pre + (ar ? 'en' : 'ar') + '/mynaghi/index.html">' + (ar ? 'English' : 'العربية') + '</a>' +
            '</div>';
        var aside = document.createElement('aside');
        aside.className = 'dps-drawer';
        aside.id = 'site-menu';
        aside.setAttribute('aria-label', ar ? 'القائمة' : 'Menu');
        aside.innerHTML =
            '<div class="dps-drawer-head dps-modal-head"><h2>' + (ar ? 'القائمة' : 'Menu') + '</h2>' +
            '<button type="button" class="dps-x" data-close="1" aria-label="' + (ar ? 'إغلاق' : 'Close') + '">&times;</button></div>' +
            '<div class="dps-drawer-body">' + rows + links + '</div>';
        document.body.appendChild(aside);
    }

    /* The featured-models carousel mounts its car cutouts (and its click
       navigation) with script on the live site, so the capture holds cards
       with a name and no car. Models the site publishes a cutout for get it
       back; every card becomes the door to its own page. */
    function dressModelCards() {
        if (!window.Catalog) return;
        var pre = sitePrefix();
        var lang = langCode();
        $$('.model-card').forEach(function (card) {
            var label = (card.getAttribute('models_name') || '').trim().toLowerCase();
            if (!label) return;
            var model = null;
            window.Catalog.all().forEach(function (c) {
                if (model) return;
                if (c.nameEn.toLowerCase() === label || c.nameAr.toLowerCase() === label ||
                    c.id === label) model = c;
            });
            if (!model) return;
            if (model.image && !card.querySelector('img')) {
                var img = document.createElement('img');
                img.src = pre + model.image;
                img.alt = model.name;
                img.style.cssText = 'position:absolute;left:0;right:0;top:50%;' +
                    'transform:translateY(-40%);width:100%;max-height:62%;' +
                    'object-fit:contain;pointer-events:none;';
                card.appendChild(img);
            }
            card.style.cursor = 'pointer';
            card.addEventListener('click', function () {
                location.href = pre + lang + '/mynaghi/models/' + model.path + '/index.html';
            });
        });
    }

    function wireHeaderMenus() {
        var header = $('header.site-header');
        if (!header) return;

        var hovering = false;
        var openLi = null;
        var closeTimer = null;

        function paintState() {
            var scrolled = (window.scrollY || 0) > 24;
            header.classList.toggle('force-hovered', hovering || scrolled || !!openLi);
        }

        function closeMenu() {
            if (!openLi) return;
            var wrap = $('.dropdown_menu_wrapper', openLi);
            var btn = $('button[aria-haspopup]', openLi);
            if (wrap) wrap.style.height = '0px';
            if (btn) btn.setAttribute('aria-expanded', 'false');
            openLi = null;
            paintState();
        }

        function openMenu(li) {
            if (openLi === li) return;
            closeMenu();
            var wrap = $('.dropdown_menu_wrapper', li);
            var btn = $('button[aria-haspopup]', li);
            if (!wrap) return;
            wrap.style.height = wrap.scrollHeight + 'px';
            if (btn) btn.setAttribute('aria-expanded', 'true');
            openLi = li;
            paintState();
        }

        $$('button[aria-haspopup]', header).forEach(function (btn) {
            var li = btn.closest('li');
            if (!li || !$('.dropdown_menu_wrapper', li)) return;
            btn.setAttribute('aria-expanded', 'false');
            btn.addEventListener('click', function (event) {
                event.preventDefault();
                event.stopPropagation();
                if (openLi === li) { closeMenu(); } else { openMenu(li); }
            });
            li.addEventListener('mouseenter', function () {
                window.clearTimeout(closeTimer);
                openMenu(li);
            });
            li.addEventListener('mouseleave', function () {
                window.clearTimeout(closeTimer);
                closeTimer = window.setTimeout(closeMenu, 220);
            });
        });

        header.addEventListener('mouseenter', function () { hovering = true; paintState(); });
        header.addEventListener('mouseleave', function () { hovering = false; paintState(); });
        window.addEventListener('scroll', paintState, { passive: true });
        document.addEventListener('click', function (event) {
            if (openLi && !openLi.contains(event.target)) closeMenu();
        });
        document.addEventListener('keydown', function (event) {
            if (event.key === 'Escape') closeMenu();
        });
        paintState();

        /* Find a Car opens a scripted finder on the live site; the model grid
           on the tenant home is this replica's finder. */
        var lang = langCode();
        var pre = sitePrefix();
        $$('li > span.cursor-pointer', header).forEach(function (el) {
            var label = el.textContent.trim();
            if (label !== 'Find a Car' && label.indexOf('بحث عن سيارة') === -1 &&
                label.indexOf('ابحث عن سيارة') === -1) return;
            el.addEventListener('click', function () {
                var grid = $('#dn_inline_target_in_grid');
                if (grid) { grid.scrollIntoView({ behavior: 'smooth', block: 'center' }); return; }
                location.href = pre + lang + '/mynaghi/index.html';
            });
        });

        /* The location chip routes to the regional gateway; the login button
           gets the same notice as any other page the demo does not carry;
           both burgers open the site map. */
        $$('button', header).forEach(function (btn) {
            if (/^(Jeddah|جدة)$/.test(btn.textContent.trim())) {
                btn.addEventListener('click', function () { location.href = pre + 'index.html'; });
            }
        });
        var login = $('.profile_button', header);
        if (login) login.setAttribute('data-demo-dead', '1');
        buildSiteMenu();
        $$('.menu_toggler, .menu_close_icon', header).forEach(function (btn) {
            btn.setAttribute('data-open', '#site-menu');
        });
    }

    /* The 17 shared popup creatives render in cross-origin iframes and ask the
       host page for its theme. Answer with Hyundai's, so every one of them
       arrives dressed in Hyundai blue. Protocol from the factory's boot.js. */
    var THEME = {
        primary: '#002c5f', onPrimary: '#ffffff', accent: '#e63312',
        ink: '#0e1215', muted: '#6e7275', surface: '#ffffff', page: '#f5f5f5',
        line: '#ebebeb', tint: '#eef3f8', radius: '4px',
        brandText: '#002c5f', shadow: '0 12px 32px rgba(0,0,0,.16)',
        displayFont: '"HyundaiMedium", Arial, sans-serif',
        bodyFont: '"HyundaiRegular", Arial, sans-serif'
    };

    function answerThemeRequests() {
        window.addEventListener('message', function (event) {
            if (!event.data || event.data.dnTheme !== 'request') return;
            if (!event.source) return;
            try { event.source.postMessage({ dnTheme: 'reply', theme: THEME }, '*'); }
            catch (err) { /* a frame that has already gone is not an error */ }
        });
    }

    /* ------------------------------------------------------------------ */
    /* Boot                                                                */

    function pageviewDetail() {
        var body = document.body;
        return {
            productId: body.getAttribute('data-product-id') || undefined,
            price: body.getAttribute('data-price') || undefined,
            categoryPath: body.getAttribute('data-category-path') || undefined,
            promotionId: body.getAttribute('data-promotion-id') || undefined
        };
    }

    /* A static capture can carry the odd img whose source never existed on
       the CDN. A broken-image glyph reads as a fault, an absent one as
       design, so failures simply disappear. */
    function hideBrokenImages() {
        document.addEventListener('error', function (event) {
            var el = event.target;
            if (el && el.tagName === 'IMG') el.style.visibility = 'hidden';
        }, true);
        $$('img').forEach(function (img) {
            if (img.complete && img.naturalWidth === 0 && img.getAttribute('src')) {
                img.style.visibility = 'hidden';
            }
        });
    }

    function boot() {
        /* FIRST, before anything else on the page: the page view is the only
           thing that makes this demo's rows findable in the shared tables. */
        window.DengageEvents.pageview(
            document.body.getAttribute('data-page-type') || 'other', pageviewDetail());

        hideBrokenImages();

        answerThemeRequests();
        wireOverlays();
        wireHeaderMenus();
        wireUniversalCtas();
        wireGallery();
        dressModelCards();
        wireFunnelButtons();
        wireCarousels();
        wireDragRails();
        wireArrows();
        wireSelects();
        wireChoiceChips();
        wireShowroomMap();
        wireAccordions();
        wireTabs();
        wireCountdowns();
        wireDeadLinks();
        wireLeadForms();
        hideColorConfigurators();
        dressFooter();
        dressServicePage();
        paintHearts();

        if (window.Panels) window.Panels.init();
        if (window.Slots) window.Slots.init();
        if (window.Inbox) window.Inbox.boot();
    }

    window.Storefront = {
        t: t,
        openOverlay: openOverlay,
        closeOverlays: closeOverlays,
        boot: boot
    };
    window.Site = {
        cartLines: cartLines,
        openTestDrive: openTestDrive,
        saved: wishlist
    };

    function bootOnce() {
        if (window.__dpsBooted) return;
        window.__dpsBooted = true;
        boot();
    }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', bootOnce);
    } else {
        bootOnce();
    }
})(window, document);
