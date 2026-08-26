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
            show(0); auto();
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
        $$('button[aria-label="Inquire Now"], button[aria-label="اطلبه الآن"]').forEach(function (btn) {
            btn.addEventListener('click', function () {
                location.href = pre + lang + '/mynaghi/contact-us/index.html';
            });
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
        dressModelCards();
        wireFunnelButtons();
        wireCarousels();
        wireAccordions();
        wireTabs();
        wireCountdowns();
        wireDeadLinks();
        wireLeadForms();
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
