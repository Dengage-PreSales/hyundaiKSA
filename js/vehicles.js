/* ============================================================================
   The vehicle catalogue of D·Auto, a fictitious automotive brand built for
   product demonstrations. Every model name, price and specification here is
   invented; the lineup deliberately spans the segments a real national
   distributor carries (city cars to family vans) so every automotive use
   case has a natural home.

   The read API mirrors the factory template's Catalog surface so js/panels.js
   works unchanged: all, get, effectivePrice, search, escapeAttr.
   ========================================================================== */
(function (window, document) {
    'use strict';

    var MODELS = [
        { id: 'pulse',           name: { en: 'PULSE',           ar: 'بولس' },           category: 'Sedan', price: 71484,  pdp: true },
        { id: 'sovereign',       name: { en: 'SOVEREIGN',       ar: 'سوفرين' },         category: 'Sedan', price: 158436, pdp: true },
        { id: 'vector',          name: { en: 'VECTOR',          ar: 'فكتور' },          category: 'Sedan', price: 86694,  pdp: true },
        { id: 'neo',             name: { en: 'NEO',             ar: 'نيو' },            category: 'Sedan', price: 56239,  pdp: true },
        { id: 'serene',          name: { en: 'SERENE',          ar: 'سيرين' },          category: 'Sedan', price: 107904, pdp: true },
        { id: 'terra',           name: { en: 'TERRA',           ar: 'تيرا' },           category: 'SUV',   price: 86200,  pdp: true },
        { id: 'terra-max',       name: { en: 'TERRA MAX',       ar: 'تيرا ماكس' },      category: 'SUV',   price: 102054, pdp: true },
        { id: 'apex',            name: { en: 'APEX',            ar: 'أبكس' },           category: 'SUV',   price: 92544,  pdp: true },
        { id: 'summit',          name: { en: 'SUMMIT',          ar: 'سوميت' },          category: 'SUV',   price: 177039, pdp: true },
        { id: 'ridge',           name: { en: 'RIDGE',           ar: 'ريدج' },           category: 'SUV',   price: 138429, pdp: true },
        { id: 'vanta',           name: { en: 'VANTA',           ar: 'فانتا' },          category: 'SUV',   price: 101258, pdp: true },
        { id: 'urban',           name: { en: 'URBAN',           ar: 'أوربان' },         category: 'SUV',   price: 77334,  pdp: true },
        { id: 'nova',            name: { en: 'NOVA',            ar: 'نوفا' },           category: 'MPV',   price: 79147,  pdp: true },
        { id: 'voyager-premium', name: { en: 'VOYAGER Premium', ar: 'فوياجر بريميوم' }, category: 'MPV',   price: 180294, pdp: true },
        { id: 'voyager-van',     name: { en: 'VOYAGER Van',     ar: 'فوياجر فان' },     category: 'MPV',   price: null,   pdp: true },
        { id: 'voyager',         name: { en: 'VOYAGER',         ar: 'فوياجر' },         category: 'MPV',   price: 136224, pdp: true }
    ];

    /* Brand artwork per model: a scene card from the D·Auto visual system,
       varied by body style and palette so the range reads as a range, plus a
       transparent cutout per body style for the model cards. The paths are
       spelled out in full because the asset pruner keeps whatever these
       literal strings reference: assets/brand/cut-sedan.svg,
       assets/brand/cut-suv.svg, assets/brand/cut-van.svg. */
    var CUT = { Sedan: 'assets/brand/cut-sedan.svg', SUV: 'assets/brand/cut-suv.svg', MPV: 'assets/brand/cut-van.svg' };

    var ART = {
        'pulse':           'assets/brand/scene-sedan-1.svg',
        'sovereign':       'assets/brand/scene-sedan-2.svg',
        'vector':          'assets/brand/scene-sedan-3.svg',
        'neo':             'assets/brand/scene-sedan-4.svg',
        'serene':          'assets/brand/scene-sedan-1.svg',
        'terra':           'assets/brand/scene-suv-1.svg',
        'terra-max':       'assets/brand/scene-suv-2.svg',
        'apex':            'assets/brand/scene-suv-3.svg',
        'summit':          'assets/brand/scene-suv-4.svg',
        'ridge':           'assets/brand/scene-suv-1.svg',
        'vanta':           'assets/brand/scene-suv-2.svg',
        'urban':           'assets/brand/scene-suv-3.svg',
        'nova':            'assets/brand/scene-van-1.svg',
        'voyager-premium': 'assets/brand/scene-van-2.svg',
        'voyager-van':     'assets/brand/scene-van-3.svg',
        'voyager':         'assets/brand/scene-van-4.svg'
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
            image: ART[model.id] || null,
            cutout: CUT[model.category] || null,
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
