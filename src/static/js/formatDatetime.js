function formatDatetime(datetimeObj, options) {
  if (!datetimeObj) {
    return "-";
  }

  var defaultOptions = { 
    year: 'numeric', month: 'numeric', day: 'numeric',
    hour: 'numeric', minute: 'numeric', second: 'numeric',
    timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone
  };

  options = Object.assign({}, defaultOptions, options);
  return datetimeObj.toLocaleString('ru-RU', options);
}

function initDatetimeFormatting() {
  var datetimeElements = document.querySelectorAll('.datetime-field');
  datetimeElements.forEach(function(element) {
    var datetimeObj = new Date(element.dataset.datetimeObj);
    var options = JSON.parse(element.dataset.datetimeOptions || '{}');
    element.textContent = formatDatetime(datetimeObj, options);
  });
}

document.addEventListener('DOMContentLoaded', initDatetimeFormatting);