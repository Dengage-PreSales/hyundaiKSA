/* ============================================================================
   Strings for the Dengage demo controls, in both site languages. The replica's
   own page copy is baked into each HTML file, because the page IS the content;
   these strings belong to the launcher, the inbox drawer and the event panel,
   which are shared across every page.

   Key names follow the factory modules that read them (js/panels.js and
   js/inbox.js), so those files port with their reading code unchanged. Read at
   call time, never captured at module scope: the html lang attribute is the
   source of truth and each page sets its own.
   ========================================================================== */
(function (window, document) {
    'use strict';

    var STRINGS = {
        en: {
            launcherOpen: 'Dengage demo',
            launcherTitle: 'Dengage scenarios',
            launcherIntro: 'Fire any experience on this page, live. Everything lands in the Dengage panel as it happens.',
            launcherReset: 'Reset widget display state',
            groupBrand: 'D·Auto scenarios',
            groupOnsite: 'On-site messaging',
            groupAbTest: 'A/B testing',
            groupGame: 'Gamification',
            groupInline: 'Inline personalization',
            groupPush: 'Web push',
            groupInbox: 'App inbox',
            groupEvents: 'Data events',
            inlineElsewhere: 'Renders on another page of this demo',
            gestureExitIntent: 'Move the pointer up and out of the page to trigger it',
            gestureScrollDepth: 'Scroll down the page to trigger it',
            actionPushPrompt: 'Raises the browser permission prompt',
            actionInboxOpen: 'Opens the message drawer',
            setupNote: 'One-off campaign: paste from panel/ in this repository if it does not appear',
            quickRef: 'Quick reference',
            refDevice: 'Device id',
            refSession: 'Session id',
            refToken: 'Push token',
            refContact: 'Contact key',
            refPageUrl: 'Demo page URL',
            refAccount: 'Account',
            refApp: 'Application',
            refNone: 'not available yet',
            refCopy: 'Copy',
            refCopied: 'Copied',
            eventsTitle: 'Storefront events',
            eventsIntro: 'Send a real ecommerce event to Dengage, exactly as the site itself does.',
            eventSend: 'Send event',
            inboxTitle: 'D·Auto updates',
            inboxJustNow: 'just now',
            inboxMinutes: '{n} min ago',
            inboxHours: '{n} h ago',
            inboxUnread: '{n} unread',
            inboxNoSdk: 'This page is not connected to a Dengage application.',
            inboxStarting: 'Connecting to your inbox. Press Refresh in a moment.',
            inboxError: 'Dengage could not return this inbox. The console has the reason.',
            inboxEmpty: 'No messages yet.',
            inboxEmptyHint: 'Send one from a Dengage campaign or journey, then press Refresh.',
            inboxUntitled: 'Untitled message',
            inboxOpen: 'Open',
            inboxDismiss: 'Dismiss',
            inboxRefresh: 'Refresh',
            close: 'Close',
            testDrive: 'Book a Test Drive',
            tdChooseTrim: 'Choose your version',
            tdYourDetails: 'Your details',
            tdName: 'Full name',
            tdMobile: 'Mobile number',
            tdCity: 'City',
            tdSubmit: 'Confirm booking',
            tdThanks: 'Your test drive request is in. Our team will call you to confirm the time.',
            tdContinue: 'Continue',
            notPart: 'This link is outside the scope of this demo.'
        },
        ar: {
            launcherOpen: 'عرض دنقيج',
            launcherTitle: 'سيناريوهات دنقيج',
            launcherIntro: 'شغّل أي تجربة على هذه الصفحة مباشرة. كل شيء يصل إلى لوحة دنقيج لحظة حدوثه.',
            launcherReset: 'إعادة تعيين حالة الودجات',
            groupBrand: 'سيناريوهات دي أوتو',
            groupOnsite: 'رسائل الموقع',
            groupAbTest: 'اختبار A/B',
            groupGame: 'التلعيب',
            groupInline: 'تخصيص مدمج',
            groupPush: 'إشعارات الويب',
            groupInbox: 'صندوق الرسائل',
            groupEvents: 'أحداث البيانات',
            inlineElsewhere: 'يظهر في صفحة أخرى من هذا العرض',
            gestureExitIntent: 'حرّك المؤشر خارج الصفحة من الأعلى لتشغيله',
            gestureScrollDepth: 'مرّر إلى أسفل الصفحة لتشغيله',
            actionPushPrompt: 'يعرض طلب إذن الإشعارات في المتصفح',
            actionInboxOpen: 'يفتح درج الرسائل',
            setupNote: 'حملة مخصصة: الصقها من مجلد panel/ في المستودع إذا لم تظهر',
            quickRef: 'مرجع سريع',
            refDevice: 'معرّف الجهاز',
            refSession: 'معرّف الجلسة',
            refToken: 'رمز الإشعارات',
            refContact: 'مفتاح جهة الاتصال',
            refPageUrl: 'رابط صفحة العرض',
            refAccount: 'الحساب',
            refApp: 'التطبيق',
            refNone: 'غير متوفر بعد',
            refCopy: 'نسخ',
            refCopied: 'تم النسخ',
            eventsTitle: 'أحداث المتجر',
            eventsIntro: 'أرسل حدث تجارة إلكترونية حقيقياً إلى دنقيج، تماماً كما يفعل الموقع نفسه.',
            eventSend: 'إرسال الحدث',
            inboxTitle: 'تحديثات دي أوتو',
            inboxJustNow: 'الآن',
            inboxMinutes: 'قبل {n} دقيقة',
            inboxHours: 'قبل {n} ساعة',
            inboxUnread: '{n} غير مقروءة',
            inboxNoSdk: 'هذه الصفحة غير متصلة بتطبيق دنقيج.',
            inboxStarting: 'جارٍ الاتصال بصندوق الوارد. اضغط تحديث بعد لحظات.',
            inboxError: 'تعذر على دنقيج إرجاع صندوق الوارد. التفاصيل في وحدة التحكم.',
            inboxEmpty: 'لا توجد رسائل بعد.',
            inboxEmptyHint: 'أرسل رسالة من حملة أو رحلة في دنقيج ثم اضغط تحديث.',
            inboxUntitled: 'رسالة بلا عنوان',
            inboxOpen: 'فتح',
            inboxDismiss: 'إخفاء',
            inboxRefresh: 'تحديث',
            close: 'إغلاق',
            testDrive: 'احجز تجربة قيادة',
            tdChooseTrim: 'اختر الفئة',
            tdYourDetails: 'بياناتك',
            tdName: 'الاسم الكامل',
            tdMobile: 'رقم الجوال',
            tdCity: 'المدينة',
            tdSubmit: 'تأكيد الحجز',
            tdThanks: 'تم استلام طلب تجربة القيادة. سيتصل بك فريقنا لتأكيد الموعد.',
            tdContinue: 'متابعة',
            notPart: 'هذا الرابط خارج نطاق هذا العرض.'
        }
    };

    function table() {
        var lang = (document.documentElement.getAttribute('lang') || 'en').indexOf('ar') === 0 ? 'ar' : 'en';
        return STRINGS[lang] || STRINGS.en;
    }

    window.SiteCopy = {
        table: table,
        t: function (key, vars) {
            var value = table()[key];
            if (value === undefined) value = STRINGS.en[key];
            if (value === undefined) return key;
            Object.keys(vars || {}).forEach(function (name) {
                value = value.replace('{' + name + '}', vars[name]);
            });
            return value;
        }
    };
})(window, document);
