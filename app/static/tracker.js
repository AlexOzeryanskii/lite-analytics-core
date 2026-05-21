(function () {
    "use strict";

    var script = document.currentScript;
    if (!script) {
        return;
    }

    var projectKey = script.getAttribute("data-project-key");
    if (!projectKey) {
        return;
    }

    var backendUrl = (script.getAttribute("data-backend-url") || window.location.origin).replace(/\/$/, "");
    var swPath = script.getAttribute("data-sw-path") || "/sw.js";
    var vapidPublicKey = script.getAttribute("data-vapid-public-key") || "";

    function randomId(prefix) {
        try {
            return prefix + "_" + Math.random().toString(36).slice(2, 10) + Date.now().toString(36);
        } catch (e) {
            return prefix + "_fallback";
        }
    }

    function getVisitorId() {
        try {
            var stored = localStorage.getItem("la_visitor_id");
            if (!stored) {
                stored = randomId("vis");
                localStorage.setItem("la_visitor_id", stored);
            }
            return stored;
        } catch (e) {
            return randomId("vis");
        }
    }

    function getSessionId() {
        try {
            var stored = sessionStorage.getItem("la_session_id");
            if (!stored) {
                stored = randomId("sess");
                sessionStorage.setItem("la_session_id", stored);
            }
            return stored;
        } catch (e) {
            return randomId("sess");
        }
    }

    function basePayload() {
        try {
            return {
                project_key: projectKey,
                path: window.location.pathname + window.location.search,
                title: document.title || null,
                referrer: document.referrer || null,
                session_id: getSessionId(),
                visitor_id: getVisitorId(),
                screen_width: window.screen ? window.screen.width : null,
                screen_height: window.screen ? window.screen.height : null,
                language: navigator.language || null,
                timezone: (Intl.DateTimeFormat && Intl.DateTimeFormat().resolvedOptions().timeZone) || null
            };
        } catch (e) {
            return {
                project_key: projectKey,
                path: "/",
                title: null,
                referrer: null,
                session_id: randomId("sess"),
                visitor_id: randomId("vis"),
                screen_width: null,
                screen_height: null,
                language: null,
                timezone: null
            };
        }
    }

    function sendRequest(url, payload) {
        var body;
        try {
            body = JSON.stringify(payload);
        } catch (e) {
            return;
        }

        try {
            if (navigator.sendBeacon) {
                var blob = new Blob([body], { type: "application/json" });
                if (navigator.sendBeacon(url, blob)) {
                    return;
                }
            }
        } catch (e) {
            // fall through to fetch
        }

        try {
            if (typeof fetch === "function") {
                fetch(url, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: body,
                    keepalive: true,
                    credentials: "omit"
                }).catch(function () {});
            }
        } catch (e) {
            // Never break the host page
        }
    }

    function track(eventType, customPayload) {
        try {
            var payload = basePayload();
            payload.event_type = eventType;
            if (customPayload && typeof customPayload === "object") {
                payload.payload = customPayload;
            }
            sendRequest(backendUrl + "/api/track", payload);
        } catch (e) {
            // Never break the host page
        }
    }

    function urlBase64ToUint8Array(base64String) {
        var padding = "=".repeat((4 - (base64String.length % 4)) % 4);
        var base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
        var rawData = window.atob(base64);
        var outputArray = new Uint8Array(rawData.length);
        for (var i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }
        return outputArray;
    }

    function subscribePush() {
        if (!("serviceWorker" in navigator) || !("PushManager" in window)) {
            return Promise.reject(new Error("Push notifications are not supported in this browser"));
        }
        if (!vapidPublicKey) {
            return Promise.reject(new Error("data-vapid-public-key is required for push subscription"));
        }

        return navigator.serviceWorker
            .register(swPath)
            .then(function (registration) {
                return Notification.requestPermission().then(function (permission) {
                    if (permission !== "granted") {
                        throw new Error("Notification permission was not granted");
                    }
                    return registration.pushManager.getSubscription().then(function (subscription) {
                        if (!subscription) {
                            return registration.pushManager.subscribe({
                                userVisibleOnly: true,
                                applicationServerKey: urlBase64ToUint8Array(vapidPublicKey)
                            });
                        }
                        return subscription;
                    });
                });
            })
            .then(function (subscription) {
                var json = subscription.toJSON();
                return fetch(backendUrl + "/api/push/subscribe", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        project_key: projectKey,
                        endpoint: json.endpoint,
                        keys: {
                            p256dh: json.keys.p256dh,
                            auth: json.keys.auth
                        }
                    }),
                    credentials: "omit"
                }).then(function (response) {
                    if (!response.ok) {
                        throw new Error("Failed to save push subscription");
                    }
                    return subscription;
                }).catch(function () {
                    throw new Error("Failed to save push subscription");
                });
            });
    }

    window.LiteAnalytics = {
        track: track,
        subscribePush: subscribePush,
        projectKey: projectKey
    };

    try {
        if (document.readyState === "complete") {
            track("pageview");
        } else {
            window.addEventListener("load", function () {
                track("pageview");
            });
        }
    } catch (e) {
        // Never break the host page
    }
})();
