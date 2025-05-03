async function request(method, params) {
  return new Promise((resolve, reject) => {
    const httpMethod = $httpClient[method.toLowerCase()];
    httpMethod(params, (error, response, data) => {
      resolve({ error, response, data });
    });
  });
}

async function checkTitle(id) {
  const { error, response, data } = await request(
    "GET",
    `https://www.netflix.com/title/${id}`
  );

  if (error) {
    return "";
  }

  if (response.headers["X-Robots-Tag"] === "index") {
    return "us";
  }
  if (response.headers["Location"]) {
    const loc = response.headers["Location"].split("/")[3];
    return loc.split("-")[0];
  }
  return "";
}

async function main() {
  var country = await checkTitle(70143836);
  if (country) {
    $done({
      content: `No Restriction (${country.toUpperCase()})`,
      backgroundColor: "#E50914",
    });
    return;
  }

  var country = await checkTitle(80197526);
  if (country) {
    $done({
      content: `Originals Only (${country.toUpperCase()})`,
      backgroundColor: "#E50914",
    });
    return;
  }

  $done({
    content: "Not Available",
    backgroundColor: "",
  });
}

(async () => {
  main()
    .then((_) => {})
    .catch((error) => {
      $done({});
    });
})();
