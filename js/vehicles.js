/* ============================================================================
   The vehicle catalogue: every model hyundaiksa.com sells through Mynaghi,
   with names in both site languages and the starting price each model page
   actually displays (SAR, including 15 percent VAT), read from the live pages
   on 26 August 2026.

   A model whose page shows no price carries price: null, and the event layer
   drops null keys rather than sending them. Never write a number here that
   the site did not display: an invented price would land in shared Dengage
   tables where nothing can tell it from a real one.

   The read API mirrors the factory template's Catalog surface so js/panels.js
   works unchanged: all, get, effectivePrice, search, escapeAttr.
   ========================================================================== */
(function (window, document) {
    'use strict';

    var MODELS = [
        { id: 'accent',         name: { en: 'ACCENT',           ar: 'أكسنت' },          category: 'Sedan', price: 71484 , pdp: true },
        { id: 'azera',          name: { en: 'AZERA',            ar: 'أزيرا' },          category: 'Sedan', price: 158436 , pdp: true },
        { id: 'elantra',        name: { en: 'ELANTRA',          ar: 'النترا' },         category: 'Sedan', price: 86694,  path: 'Elantra' , pdp: true },
        { id: 'grandi10',       name: { en: 'GRAND i10',        ar: 'جراند i10' },      category: 'Sedan', price: 56239 , pdp: true },
        { id: 'sonata',         name: { en: 'SONATA',           ar: 'سوناتا' },         category: 'Sedan', price: 107904 , pdp: true },
        { id: 'creta',          name: { en: 'CRETA',            ar: 'كريتا' },          category: 'SUV',   price: 86200 , pdp: true },
        { id: 'creta-grand',    name: { en: 'CRETA GRAND',      ar: 'كريتا جراند' },    category: 'SUV',   price: 102054 , pdp: true },
        { id: 'kona',           name: { en: 'KONA',             ar: 'كونا' },           category: 'SUV',   price: 92544 , pdp: true },
        { id: 'palisade',       name: { en: 'PALISADE',         ar: 'باليسيد' },        category: 'SUV',   price: 177039 , pdp: true },
        { id: 'santa-fe',       name: { en: 'SANTA FE',         ar: 'سانتافي' },        category: 'SUV',   price: 138429, pdp: true },
        { id: 'tucson',         name: { en: 'TUCSON',           ar: 'توسان' },          category: 'SUV',   price: 101258, pdp: true },
        { id: 'venue',          name: { en: 'VENUE',            ar: 'فينيو' },          category: 'SUV',   price: 77334 , pdp: true },
        { id: 'stargazer',      name: { en: 'STARGAZER',        ar: 'ستارجايزر' },      category: 'MPV',   price: 79147 , pdp: true },
        { id: 'staria-premium', name: { en: 'STARIA Premium',   ar: 'ستاريا بريميوم' }, category: 'MPV',   price: 180294 , pdp: true },
        { id: 'staria-van',     name: { en: 'STARIA Van',       ar: 'ستاريا فان' },     category: 'MPV',   price: null , pdp: true },
        { id: 'staria-wagon',   name: { en: 'STARIA Passenger', ar: 'ستاريا واجن' },    category: 'MPV',   price: 136224 , pdp: true }
    ];

    /* A card image for every model, all served by the site itself: the
       car-finder cutouts where the site publishes one, the model's own
       page banner otherwise. Paths are spelled out in full because the
       asset pruner keeps whatever these literal strings reference. */
    var CUTOUTS = {
        'grandi10':       'assets/img/cdn/cmssection/38622/Banner-des-grand-(1)-copy.webp',
        'sonata':         'assets/img/cdn/cmssection/18522/Banner-des-(4)-(1).webp',
        'creta-grand':    'assets/img/cdn/cmssection/34258/Banner-des-(4).webp',
        'kona':           'assets/img/cdn/cmssection/33818/final-banne.webp',
        'venue':          'assets/img/cdn/cmssection/48029/home-vineu-banner.webp',
        'staria-premium': 'assets/img/cdn/cmssection/37693/final-banner-des-staria-.webp',
        'staria-van':     'assets/img/cdn/cmssection/37710/final-banner-des-van-1.webp',
        'staria-wagon':   'assets/img/cdn/cmssection/37748/Gallery-card-2-(1).webp',
        'accent':    'assets/img/cdn/vehiclemodel/29285/Hyundai-ACCENT.webp',
        'creta':     'assets/img/cdn/vehiclemodel/29319/Hyundai-CRETA.webp',
        'elantra':   'assets/img/cdn/vehiclemodel/29325/Hyundai-ELANTRA.webp',
        'santa-fe':  'assets/img/cdn/vehiclemodel/29333/Hyundai-SANTA-FE.webp',
        'tucson':    'assets/img/cdn/vehiclemodel/29411/Hyundai-TUCSON.webp',
        'azera':     'assets/img/cdn/vehiclemodel/29419/Hyundai-AZERA.webp',
        'palisade':  'assets/img/cdn/vehiclemodel/29428/Hyundai-PALISADE.webp',
        'stargazer': 'assets/img/cdn/vehiclemodel/48524/Hyundai-STARGAZER.webp'
    };

    function lang() {
        return (document.documentElement.getAttribute('lang') || 'en').indexOf('ar') === 0 ? 'ar' : 'en';
    }

    function decorate(model) {
        if (!model) return null;
        return {
            id: model.id,
            name: model.name[lang()] || model.name.en,
            nameEn: model.name.en,
            nameAr: model.name.ar,
            category: model.category,
            categoryPath: 'Vehicles>' + model.category,
            price: model.price,
            image: CUTOUTS[model.id] || null,
            pdp: !!model.pdp,
            path: model.path || model.id
        };
    }

    window.Catalog = {
        all: function () { return MODELS.map(decorate); },
        get: function (id) {
            for (var i = 0; i < MODELS.length; i++) {
                if (MODELS[i].id === id || MODELS[i].path === id) return decorate(MODELS[i]);
            }
            return null;
        },
        effectivePrice: function (model) {
            return model && model.price !== null && model.price !== undefined ? model.price : null;
        },
        search: function (term) {
            var q = String(term || '').toLowerCase().trim();
            if (!q) return [];
            return MODELS.filter(function (m) {
                return m.id.indexOf(q) !== -1 ||
                    m.name.en.toLowerCase().indexOf(q) !== -1 ||
                    m.name.ar.indexOf(q) !== -1 ||
                    m.category.toLowerCase().indexOf(q) !== -1;
            }).map(decorate);
        },
        escapeAttr: function (value) {
            return String(value === null || value === undefined ? '' : value)
                .replace(/&/g, '&amp;').replace(/"/g, '&quot;')
                .replace(/</g, '&lt;').replace(/>/g, '&gt;');
        }
    };
})(window, document);
