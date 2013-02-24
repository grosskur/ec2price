nv.addGraph(function() {  
  var chart = nv.models.scatterChart();

  chart.xAxis
      .axisLabel('Date')
        .tickFormat(function (d) {
          return d3.time.format('%b %d')(new Date(d));
        });

  chart.yAxis
      .axisLabel('Price ($)')
      .tickFormat(d3.format('.03f'));

  d3.select('#chart svg')
      .datum(prices())
    .transition().duration(500)
      .call(chart);

  nv.utils.windowResize(function () {
    d3.select('#chart svg').call(chart);
  });

  return chart;
});
