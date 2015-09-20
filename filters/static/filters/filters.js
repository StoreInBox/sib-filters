// Notice that filters always make requests to current URL.
// This is good enough for now.

var filters = {
    activate: function(callback) {
        $('[data-role="filter-item"]').click(function() {
            executeFilterToggle(this, callback);
        });
        $('[data-role="filter-item"]').each(function() {
            activateFilterToggle(this);
        });
        $("[data-role='filter-slider']").each(function() {
            activateSliderFilter($(this), callback);
        });
    }
};

function activateFilterToggle(item) {
    var name = $(item).attr("data-filter-field-name");
    if (name in getUrlVars()) {
        $(item).addClass('active');
    }
}

function executeFilterToggle(item, callback) {
    var name = $(item).attr("data-filter-field-name"),
        url = null;

    if ($(item).hasClass('active')) {
        url = removeGetParameter(name);
        $(item).removeClass('active');
    } else {
        url = setGetParameter(name, '1');
        $(item).addClass('active');
    }

    var countUrl = setGetParameter('count', 'on', url);
    window.history.pushState('', '', url);

    $.ajax({
        url: countUrl,
    }).done(function(data) {
        callback(data);
    });
}

function activateSliderFilter($sliderContainer, callback) {

    var sliderDiv = $sliderContainer.find('#slider'),
        maxField = $sliderContainer.find('[data-role="filter-item-max"]'),
        minField = $sliderContainer.find('[data-role="filter-item-min"]'),
        min = parseInt(sliderDiv.attr('data-min')),
        max = parseInt(sliderDiv.attr('data-max')),
        values = [min, max],
        urlVars = getUrlVars();

    if (minField.attr('data-filter-field-name') in urlVars) {
        values[0] = urlVars[minField.attr('data-filter-field-name')];
    }

    if (maxField.attr('data-filter-field-name') in urlVars) {
        values[1] = urlVars[maxField.attr('data-filter-field-name')];
    }

    function collision($div1, $div2) {
        var x1 = $div1.offset().left;
        var w1 = 40;
        var r1 = x1 + w1;
        var x2 = $div2.offset().left;
        var w2 = 40;
        var r2 = x2 + w2;

        if (r1 < x2 || x1 > r2) return false;
        return true;

    }

    function updateSearchParameter() {
        var url = setGetParameter(minField.attr("data-filter-field-name"), minField.val());
            url = setGetParameter(maxField.attr("data-filter-field-name"), maxField.val(), url);
            var countUrl = setGetParameter('count', 'on', url);
            window.history.pushState('', '', url);

            $.ajax({
                url: countUrl,
            }).done(function(data) {
                callback(data);
            });
    }

    function updateFromInputMin() {
        minField.keyup(function(e) {
            oldMax = sliderDiv.slider('values', 1 );
            newMin = $(this).val();
            sliderDiv.slider("option", "values", [newMin, oldMax]);
            updateMin(newMin);
            updateDiffLine(newMin, oldMax);
            updateSearchParameter();
        });
    }

    function updateFromInputMax() {
        maxField.keyup(function() {
            oldMin = sliderDiv.slider('values', 0 );
            newMax = $(this).val();
            sliderDiv.slider("option", "values", [oldMin, newMax]);
            updateMax(newMax);
            updateDiffLine(oldMin, newMax);
            updateSearchParameter();
        });
    }

    function updateBothValues(currenValMin, currenValMax) {
        minField.attr('value', currenValMin);
        maxField.attr('value', currenValMax);
        updateDiffLine(currenValMin, currenValMax);
    }

    function updateMax(currentValueMax) {
        $sliderContainer.find('.ui-slider-range').find('span.price-range-both')
        .attr('data-highprice', currentValueMax);
        $sliderContainer.find('.ui-slider-handle:eq(1)').html('<span class="price-range-max value">' +
            currentValueMax + '</span>');
    }

    function updateMin(currentValueMin) {
        $sliderContainer.find('.ui-slider-range').find('span.price-range-both')
        .attr('data-highprice', currentValueMin);
        $sliderContainer.find('.ui-slider-handle:eq(0)').html('<span class="price-range-min value">' +
            currentValueMin + '</span>');
    }

    function updateDiffLine(currentValueMin, currentValueMax) {
        $sliderContainer.find('.ui-slider-range').html('<span class="price-range-both value"><i>' +
            currentValueMin + ' - ' + currentValueMax + '</i></span>');
        $sliderContainer.find('#range-both').html('<span class="price-range-both value">' + currentValueMin +
            ' - ' + currentValueMax + '</span>');
    }

    sliderDiv.slider({
        range: true,
        min: min,
        max: max,
        values: values,
        slide: function(event, ui) {

            var maxPriceRange =  $sliderContainer.find('.price-range-max'),
                minPriceRange =  $sliderContainer.find('.price-range-min');

            minPriceRange.text(ui.values[ 0 ] + '');
            maxPriceRange.text(ui.values[ 1 ] + '');

            updateBothValues(ui.values[ 0 ], ui.values[ 1 ]);

            if (collision(minPriceRange, maxPriceRange) === true) {
                $sliderContainer.find('.price-range-min, .price-range-max').css('opacity', '0');
            } else {
                $sliderContainer.find('.price-range-min, .price-range-max').css('opacity', '1');
            }

        },
        stop: function(event, ui) {
            minField.val(ui.values[0]);
            maxField.val(ui.values[1]);

            updateSearchParameter();
        }

    });

    valueMin = sliderDiv.slider('values', 0 );
    valueMax = sliderDiv.slider('values', 1 );

    updateMin(valueMin);
    updateMax(valueMax);
    updateBothValues(valueMin, valueMax);
    updateFromInputMin();
    updateFromInputMax();
}


// Helpers:

function setGetParameter(paramName, paramValue, url) {
    // returns current url with additional get parameter
    url = url || window.location.href;
    if (url.indexOf(paramName + '=') >= 0)
    {
        var prefix = url.substring(0, url.indexOf(paramName)),
        suffix = url.substring(url.indexOf(paramName));

        suffix = suffix.substring(suffix.indexOf('=') + 1);
        suffix = (suffix.indexOf('&') >= 0) ? suffix.substring(suffix.indexOf('&')) : '';
        url = prefix + paramName + '=' + paramValue + suffix;
    } else {
        if (url.indexOf('?') < 0) {
            url += '?' + paramName + '=' + paramValue;
        } else {
            url += '&' + paramName + '=' + paramValue;
        }
    }
    return url;
}

function removeGetParameter(parameter, url) {
    url = url || window.location.href;
    //prefer to use l.search if you have a location/link object
    var urlparts = url.split('?');
    if (urlparts.length>=2 && urlparts[1]) {

        var prefix= encodeURIComponent(parameter)+'=';
        var pars= urlparts[1].split(/[&;]/g);

        //reverse iteration as may be destructive
        for (var i= pars.length; i-- > 0;) {
            //idiom for string.startsWith
            if (pars[i].lastIndexOf(prefix, 0) !== -1) {
                pars.splice(i, 1);
            }
        }
        url = urlparts[0];
        if (pars.length !== 0) {
            url +='?' + pars.join('&');
        }
        return url;
    } else {
        return url;
    }
}

// Read a page's GET URL variables and return them as an associative array.
function getUrlVars()
{
    if (window.location.href.indexOf('?') == -1) {
        return {};
    }
    var vars = [], hash;
    var hashes = window.location.href.slice(window.location.href.indexOf('?') + 1).split('&');
    for(var i = 0; i < hashes.length; i++)
    {
        hash = hashes[i].split('=');
        vars[hash[0]] = hash[1];
    }
    return vars;
}
