document.querySelectorAll(".company-field").forEach(function (field) {
  var input = field.querySelector(".company-input");
  var hiddenCode = field.querySelector(".company-code");
  var hiddenCorpname = field.querySelector(".company-corpname");
  var list = field.querySelector(".suggestions");
  var debounceTimer;

  input.addEventListener("input", function () {
    hiddenCode.value = "";
    hiddenCorpname.value = "";
    var q = input.value.trim();
    clearTimeout(debounceTimer);
    if (q.length < 2) {
      list.innerHTML = "";
      return;
    }
    debounceTimer = setTimeout(function () {
      fetch("/api/search?q=" + encodeURIComponent(q))
        .then(function (res) { return res.json(); })
        .then(function (items) {
          list.innerHTML = "";
          items.forEach(function (item) {
            var li = document.createElement("li");
            li.textContent = item.stock_code
              ? item.corp_name + " (상장 " + item.stock_code + ")"
              : item.corp_name + " (비상장)";
            li.addEventListener("click", function () {
              input.value = item.corp_name;
              hiddenCode.value = item.corp_code;
              hiddenCorpname.value = item.corp_name;
              list.innerHTML = "";
            });
            list.appendChild(li);
          });
        })
        .catch(function () { list.innerHTML = ""; });
    }, 250);
  });

  document.addEventListener("click", function (e) {
    if (!field.contains(e.target)) {
      list.innerHTML = "";
    }
  });
});
