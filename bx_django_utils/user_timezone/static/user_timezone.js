'use strict';

(() => {
    // Just store the current user time zone into a cookie
    const time_zone=Intl.DateTimeFormat().resolvedOptions().timeZone;
    document.cookie = "UserTimeZone=" + time_zone + ";path=/;samesite=Lax";
})();
