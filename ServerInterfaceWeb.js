export default class ServerInterfaceWeb {
    async request(query, data) {
        const url = "/request?query=" + encodeURIComponent(query) + "&data=" + encodeURIComponent(JSON.stringify(data));
        return new Promise((resolve) => {
            const http = new XMLHttpRequest();
            http.open("GET", url);
            http.send();
            http.timeout = 1000;

            http.addEventListener("readystatechange", () => {
                if (http.readyState == 4 && http.status == 200) {
                    resolve(JSON.parse(http.responseText));
                }
            });
        });
    }
}
