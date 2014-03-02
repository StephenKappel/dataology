//define constants to help with formatting
var LEFT_PADDING = 30,
    TOP_PADDING = 100,
    INCOME_WIDTH = 750,
    DETAIL_WIDTH = 400,
    HEIGHT = 500,
    WHITE_COL = "#B37061",
    AFR_AM_COL = "#90799C",
    HISPANIC_COL = "#0A918C",
    ASIAN_COL = "#738A2B",
    OTHER_COL = "#D35D43",
    MEDIAN_COL = "#000000",
    BOY_COL = "#3399FF",
    GIRL_COL = "#FF99FF",
    ORDER_BY_POP = 1,
    ORDER_BY_INCOME = 2,
    COLOR_BY_RACE = 1,
    COLOR_BY_GENDER = 2,
    SELECTED_COL = "#FF8000",
    UNSELECTED_COL = "#FFB266",
    TOGGLE_Y = 25,
    TOGGLE_WIDTH = 90,
    TOGGLE_HEIGHT = 25,
    TOGGLE_SPACING = 350
BAR_SPACE = 3,
BACKGROUND_COL = "#393939",
TOTAL_WIDTH = 1200,
TOTAL_HEIGHT = 715;

//define constant  to hold path to data file
var DATA_FILE = "http://rawgithub.com/stephenkappel/dataology/master/whatsitworth/whatsitworth.csv";

//initialize variables to use for storing scales
var income_scale, popularity_scale, font_scale;

var svg, rects, groups, wrappers;

//create a variable in which to store data read in from the csv file
var myData;

d3.csv(DATA_FILE, function (rawData) {

    //store data to variable so it can be accessed outside of this method
    myData = rawData;

    //make sure all of the data is typed as desired
    //(on first attempt), it appeared js was treating everything as strings)
    myData.forEach(function (d) {
        d.percentile50 = parseInt(d.percentile50);
        d.percentile25 = parseInt(d.percentile25);
        d.percentile75 = parseInt(d.percentile75);
        d.popularity = parseFloat(d.popularity);
        d.percentGradDegree = parseFloat(d.percentGradDegree);
        d.gradBoost = parseFloat(d.gradBoost);
        d.percentFemale = parseFloat(d.percentFemale);
        d.femaleMedian = parseInt(d.femaleMedian);
        d.maleMedian = parseInt(d.maleMedian);
        d.genderGap = parseInt(d.genderGap);
        d.percentWhite = parseFloat(d.percentWhite);
        d.percentAfrAm = parseFloat(d.percentAfrAm);
        d.percentHispanic = parseFloat(d.percentHispanic);
        d.percentAsian = parseFloat(d.percentAsian);
        d.percentOther = parseFloat(d.percentOther);
        d.popularityIndex = parseInt(d.popularityIndex);
        d.medianIndex = parseInt(d.medianIndex);
        d.cumPopByPop = parseFloat(d.cumPopByPop);
        d.cumPopByMedian = parseFloat(d.cumPopByMedian);
    });

    //create scale function for income (x-axis)
    income_scale = d3.scale.linear()
        .domain([25, 105])
        .rangeRound([0, INCOME_WIDTH]);

    //create a scale function for popularity (y-axis)
    popularity_scale = d3.scale.linear()
        .domain([0, 1])
        .rangeRound([0, HEIGHT]);

    //create a scale function for font size
    font_scale = d3.scale.linear()
        .domain([d3.min(myData, function (d) { return d.popularity; }),
            d3.max(myData, function (d) { return d.popularity; })])
        .rangeRound([9, 50]);

    //add an svg element in which to put my visualization
    svg = d3.select("body").select("#mySvg"); //append("svg");

    //add background
    svg.append("rect")
        .attr("fill", BACKGROUND_COL)
        .attr("width", TOTAL_WIDTH)
        .attr("height", TOTAL_HEIGHT);

    //add title
    svg.append("text")
        .attr("class", "title")
        .attr("width", TOTAL_WIDTH)
        .attr("x", Math.floor(TOTAL_WIDTH / 2))
        .attr("y", 45)
        .text("What's It Worth: The Economic Value of College Majors");

    //add source
    svg.append("a")
        .attr("xlink:href", "http://cew.georgetown.edu/whatsitworth/tables")
        .append("text")
        .attr("class", "source")
        .attr("width", TOTAL_WIDTH)
        .attr("x", Math.floor(TOTAL_WIDTH / 2))
        .attr("y", 65)
        .text("Source: Georgetown University - Center on Education and the Workforce");

    drawDetailsTextFields();

    drawToggleButtons();

    //create an x-axis for incomes
    var xAxis = d3.svg.axis()
        .scale(income_scale)
        .orient("bottom")
        .tickFormat(function (d) { return "$" + moneyFormat(d); })
        .tickSize(HEIGHT + 17 * BAR_SPACE);
    svg.append("svg:g")
        .attr("class", "axis")
        .attr("transform", "translate(" + LEFT_PADDING + ", " + TOP_PADDING + ")")
        .call(xAxis);
    svg.append("text")
        .text("Full-time annual wages (for bachelor's degree holders without a graduate degree)")
        .attr("text-anchor", "middle")
        .attr("width", INCOME_WIDTH)
        .attr("x", Math.floor(LEFT_PADDING + (INCOME_WIDTH / 2)))
        .attr("font-size", "14px")
        .attr("y", TOP_PADDING + HEIGHT + 17 * BAR_SPACE + 35);

    //create y-axis label
    svg.append("text")
        .text("Proportion of undergraduate students")
        .attr("text-anchor", "middle")
        .attr("height", HEIGHT)
        .attr("x", 30)
        .attr("font-size", "14px")
        .attr("y", 370)
        .attr("class", "yaxis");

    wrappers = svg.selectAll(".major").data(myData).enter().append("g")
        .attr("transform", function (d) { return "translate(" + LEFT_PADDING + ", " + (TOP_PADDING + popularity_scale(parseFloat(d.cumPopByMedian)) + d.medianIndex * BAR_SPACE) + ")"; })
        .attr("id", function (d) { return "wrapper" + d.popularityIndex; });

    //add background to prevent gridline from showing through
    wrappers.append("rect")
            .attr("class", "bg")
            .attr("width", function (d) { return income_scale(d.percentile75) - income_scale(d.percentile25); })
            .attr("height", function (d) { return popularity_scale(d.popularity); })
            .attr("x", function (d) { return income_scale(d.percentile25); })
            .attr("y", 0)
            .attr("fill", BACKGROUND_COL)
            .attr("stroke", BACKGROUND_COL)
            .attr("opacity", 1);

    groups = wrappers.append("g")
        .attr("class", "major")
        .attr("id", function (d) { return "major" + d.popularityIndex; });

    //create annotation elements

    var ab = svg.append("g")
        .attr("id", "annotationBar");

    //add annotation lines
    ab.append("line")
        .attr("id", "perc50Line")
        .attr("class", "annotation")
        .attr("y1", 0)
        .attr("y2", -6);
    ab.append("line")
        .attr("id", "perc75Line")
        .attr("class", "annotation")
        .attr("y1", 0)
        .attr("y2", -6);
    ab.append("line")
        .attr("id", "perc25Line")
        .attr("class", "annotation")
        .attr("y1", 0)
        .attr("y2", -6);
    ab.append("line")
        .attr("id", "maleLine")
        .attr("class", "annotation")
        .attr("y1", 0)
        .attr("y2", -6);
    ab.append("line")
        .attr("id", "femaleLine")
        .attr("class", "annotation")
        .attr("y1", 0)
        .attr("y2", -6);

    //add annotation symbols
    ab.append("text")
        .attr("id", "perc50Sym")
        .attr("class", "annotation")
        .text("½")
        .attr("y", -13);
    ab.append("text")
        .attr("id", "perc25Sym")
        .attr("class", "annotation")
        .text("¼")
        .attr("y", -13);
    ab.append("text")
        .attr("id", "perc75Sym")
        .attr("class", "annotation")
        .text("¾")
        .attr("y", -13);
    ab.append("text")
        .attr("id", "maleSym")
        .attr("class", "annotation-sym")
        .text("♂")
        .attr("y", -13);
    ab.append("text")
        .attr("id", "femaleSym")
        .attr("class", "annotation-sym")
        .text("♀")
        .attr("y", -13);

    groups.each(function (d) {

        var cumy = 0;
        var myG = d3.select("#major" + d.popularityIndex);

        //add income range boxes for each ethnicity:

        //white
        myG.append("rect")
            .attr("class", "ethnicBar")
            .attr("width", function () { return income_scale(d.percentile75) - income_scale(d.percentile25); })
            .attr("height", function () { return popularity_scale(d.popularity * d.percentWhite); })
            .attr("x", function () { return income_scale(d.percentile25); })
            .attr("y", function () { return popularity_scale(cumy); })
            .attr("fill", WHITE_COL)
            .attr("stroke", WHITE_COL)
            .attr("opacity", 0);
        cumy += (d.popularity * d.percentWhite);

        //african american
        myG.append("rect")
            .attr("class", "ethnicBar")
            .attr("width", function () { return income_scale(d.percentile75) - income_scale(d.percentile25); })
            .attr("height", function () { return popularity_scale(d.popularity * d.percentAfrAm); })
            .attr("x", function () { return income_scale(d.percentile25); })
            .attr("y", function () { return popularity_scale(cumy); })
            .attr("fill", AFR_AM_COL)
            .attr("stroke", AFR_AM_COL)
            .attr("opacity", 0);
        cumy += (d.popularity * d.percentAfrAm);

        //hispanic
        myG.append("rect")
            .attr("class", "ethnicBar")
            .attr("width", function () { return income_scale(d.percentile75) - income_scale(d.percentile25); })
            .attr("height", function () { return popularity_scale(d.popularity * d.percentHispanic); })
            .attr("x", function () { return income_scale(d.percentile25); })
            .attr("y", function () { return popularity_scale(cumy); })
            .attr("fill", HISPANIC_COL)
            .attr("stroke", HISPANIC_COL)
            .attr("opacity", 0);
        cumy += d.popularity * d.percentHispanic;

        //asian
        myG.append("rect")
            .attr("class", "ethnicBar")
            .attr("width", function () { return income_scale(d.percentile75) - income_scale(d.percentile25); })
            .attr("height", function () { return popularity_scale(d.popularity * d.percentAsian); })
            .attr("x", function () { return income_scale(d.percentile25); })
            .attr("y", function () { return popularity_scale(cumy); })
            .attr("fill", ASIAN_COL)
            .attr("stroke", ASIAN_COL)
            .attr("opacity", 0);
        cumy += d.popularity * d.percentAsian;

        //other
        myG.append("rect")
            .attr("class", "ethnicBar")
            .attr("width", function () { return income_scale(d.percentile75) - income_scale(d.percentile25); })
            .attr("height", function () { return popularity_scale(d.popularity * d.percentOther); })
            .attr("x", function () { return income_scale(d.percentile25); })
            .attr("y", function () { return popularity_scale(cumy); })
            .attr("fill", OTHER_COL)
            .attr("stroke", OTHER_COL)
            .attr("opacity", 0);
        cumy += d.popularity * d.percentOther;

        //add income ranges for genders:

        //boys bar
        myG.append("rect")
            .attr("class", "genderBar")
            .attr("width", function () { return income_scale(d.percentile75) - income_scale(d.percentile25); })
            .attr("height", function () { return popularity_scale(d.popularity * (1 - d.percentFemale)); })
            .attr("x", function () { return income_scale(d.percentile25); })
            .attr("y", 0)
            .attr("fill", BOY_COL)
            .attr("stroke", BOY_COL)
            .attr("opacity", 1);

        //girls bar
        myG.append("rect")
            .attr("class", "genderBar")
            .attr("width", function () { return income_scale(d.percentile75) - income_scale(d.percentile25); })
            .attr("height", function () { return popularity_scale(d.popularity * d.percentFemale); })
            .attr("x", function () { return income_scale(d.percentile25); })
            .attr("y", function () { return popularity_scale(d.popularity * (1 - d.percentFemale)); })
            .attr("fill", GIRL_COL)
            .attr("stroke", GIRL_COL)
            .attr("opacity", 1);

        //add labels/annotations to bars:

        //add labels for major groups
        myG.append("text")
            .attr("class", "majorName")
            .attr("height", popularity_scale(d.popularity))
            .attr("x", function () { return (income_scale(d.percentile75) + income_scale(d.percentile25)) / 2; })
            .attr("y", Math.floor((popularity_scale(d.popularity) + font_scale(d.popularity)) / 2) - 1)
            .attr("text-anchor", "middle")
            .attr("font-size", font_scale(d.popularity) + "px")
            .text(d.majorGroup);

        //add events

        //add transparent box over entire row to help handle hover events
        myG.append("rect")
            .attr("x", 0)
            .attr("y", 0)
            .attr("width", (INCOME_WIDTH))
            .attr("height", function () { return popularity_scale(d.popularity) + BAR_SPACE; })
            .attr("opacity", 0);

        //add mouseover and mouseout events to highlight data the mouse is currently over
        myG.on("mouseover", function (d) {
            var w = d3.select("#wrapper" + d.popularityIndex);
            placeAnnotations(parseYLocation(w.attr("transform")), d);
            showDetails(d);
            focus(d.popularityIndex);
        })
        .on("mouseout", function (d) {
            restoreAll();
        });

        orderBars(ORDER_BY_INCOME);
        colorBars(COLOR_BY_GENDER);
    });
});

function drawDetailsTextFields() {

    //track y position as we create fields
    var y = 0;

    //column positions
    var SYMBOL_X = 0,
        DESC_X = 35,
        DOLLAR_X = 257,
        VALUE_X = 310;

    //add group to contain all detail fields
    var detailsGroup = svg.append("g")
        .attr("id", "detailsGroup")
        .attr("width", DETAIL_WIDTH)
        .attr("transform", "translate(" + (LEFT_PADDING + INCOME_WIDTH + 20) + ", " + (TOP_PADDING + 130) + ")")
        .attr("opacity", 0);

    //title
    detailsGroup.append("text")
       .attr("font-size", "20px")
       .attr("font-weight", "bold")
       .attr("y", y)
       .attr("x", SYMBOL_X)
       .text("Major group:");
    y += 30;
    detailsGroup.append("text")
        .attr("id", "txtMajorArea")
        .attr("font-size", "20px")
        .attr("font-weight", "bold")
        .attr("y", y)
        .attr("x", SYMBOL_X);
    y += 45;

    //wages
    detailsGroup.append("text")
        .attr("class", "details")
        .text("Popularity:")
        .attr("y", y)
        .attr("x", DESC_X);
    detailsGroup.append("text")
        .attr("id", "txtPopularity")
        .attr("class", "details")
        .attr("y", y)
        .attr("x", VALUE_X)
        .attr("text-anchor", "end");
    y += 40;

    detailsGroup.append("text")
        .attr("class", "details")
        .text("¼")
        .attr("y", y)
        .attr("x", SYMBOL_X);
    detailsGroup.append("text")
        .attr("class", "details")
        .text("Lower quartile wages:")
        .attr("y", y)
        .attr("x", DESC_X);
    detailsGroup.append("text")
        .attr("class", "details")
        .text("$")
        .attr("y", y)
        .attr("x", DOLLAR_X);
    detailsGroup.append("text")
        .attr("id", "txt25Perc")
        .attr("class", "details")
        .attr("y", y)
        .attr("x", VALUE_X)
        .attr("text-anchor", "end");
    y += 25;

    detailsGroup.append("text")
        .attr("class", "details")
        .text("½")
        .attr("y", y)
        .attr("x", SYMBOL_X);
    detailsGroup.append("text")
        .attr("class", "details")
        .text("Median wages:")
        .attr("y", y)
        .attr("x", DESC_X);
    detailsGroup.append("text")
        .attr("class", "details")
        .text("$")
        .attr("y", y)
        .attr("x", DOLLAR_X);
    detailsGroup.append("text")
        .attr("id", "txt50Perc")
        .attr("class", "details")
        .attr("y", y)
        .attr("x", VALUE_X)
        .attr("text-anchor", "end");
    y += 25;

    detailsGroup.append("text")
        .attr("class", "details")
        .text("¾")
        .attr("y", y)
        .attr("x", SYMBOL_X);
    detailsGroup.append("text")
        .attr("class", "details")
        .text("Upper quartile wages:")
        .attr("y", y)
        .attr("x", DESC_X);
    detailsGroup.append("text")
        .attr("class", "details")
        .text("$")
        .attr("y", y)
        .attr("x", DOLLAR_X);
    detailsGroup.append("text")
        .attr("id", "txt75Perc")
        .attr("class", "details")
        .attr("y", y)
        .attr("x", VALUE_X)
        .attr("text-anchor", "end");
    y += 40;

    detailsGroup.append("text")
        .attr("class", "details-sym")
        .text("♂")
        .attr("y", y)
        .attr("x", SYMBOL_X);
    detailsGroup.append("text")
        .attr("class", "details")
        .text("Male median wages:")
        .attr("y", y)
        .attr("x", DESC_X);
    detailsGroup.append("text")
        .attr("class", "details")
        .text("$")
        .attr("y", y)
        .attr("x", DOLLAR_X);
    detailsGroup.append("text")
        .attr("id", "txtMaleWages")
        .attr("class", "details")
        .attr("y", y)
        .attr("x", VALUE_X)
        .attr("text-anchor", "end");
    y += 25;

    detailsGroup.append("text")
        .attr("class", "details-sym")
        .text("♀")
        .attr("y", y)
        .attr("x", SYMBOL_X);
    detailsGroup.append("text")
        .attr("class", "details")
        .text("Female median wages:")
        .attr("y", y)
        .attr("x", DESC_X);
    detailsGroup.append("text")
        .attr("class", "details")
        .text("$")
        .attr("y", y)
        .attr("x", DOLLAR_X);
    detailsGroup.append("text")
        .attr("id", "txtFemaleWages")
        .attr("class", "details")
        .attr("y", y)
        .attr("x", VALUE_X)
        .attr("text-anchor", "end");
    y += 40;

    detailsGroup.append("rect")
        .attr("class", "colorBlock")
        .attr("y", y - 14)
        .attr("x", SYMBOL_X)
        .attr("fill", BOY_COL)
        .attr("height", "15px")
        .attr("width", "15px");
    detailsGroup.append("text")
        .attr("class", "details")
        .text("Percent male:")
        .attr("y", y)
        .attr("x", DESC_X);
    detailsGroup.append("text")
        .attr("id", "txtMalePerc")
        .attr("class", "details")
        .attr("y", y)
        .attr("x", VALUE_X)
        .attr("text-anchor", "end");
    y += 25;

    detailsGroup.append("rect")
        .attr("class", "colorBlock")
        .attr("y", y - 14)
        .attr("x", SYMBOL_X)
        .attr("fill", GIRL_COL)
        .attr("height", "15px")
        .attr("width", "15px");
    detailsGroup.append("text")
        .attr("class", "details")
        .text("Percent female:")
        .attr("y", y)
        .attr("x", DESC_X);
    detailsGroup.append("text")
        .attr("id", "txtFemalePerc")
        .attr("class", "details")
        .attr("y", y)
        .attr("x", VALUE_X)
        .attr("text-anchor", "end");
    y += 40;

    detailsGroup.append("rect")
        .attr("class", "colorBlock")
        .attr("y", y - 14)
        .attr("x", SYMBOL_X)
        .attr("fill", WHITE_COL)
        .attr("height", "15px")
        .attr("width", "15px");
    detailsGroup.append("text")
        .attr("class", "details")
        .text("Percent white:")
        .attr("y", y)
        .attr("x", DESC_X);
    detailsGroup.append("text")
        .attr("id", "txtWhitePerc")
        .attr("class", "details")
        .attr("y", y)
        .attr("x", VALUE_X)
        .attr("text-anchor", "end");
    y += 25;

    detailsGroup.append("rect")
        .attr("class", "colorBlock")
        .attr("y", y - 14)
        .attr("x", SYMBOL_X)
        .attr("fill", AFR_AM_COL)
        .attr("height", "15px")
        .attr("width", "15px");
    detailsGroup.append("text")
        .attr("class", "details")
        .text("Percent African American:")
        .attr("y", y)
        .attr("x", DESC_X);
    detailsGroup.append("text")
        .attr("id", "txtAfrAmPerc")
        .attr("class", "details")
        .attr("y", y)
        .attr("x", VALUE_X)
        .attr("text-anchor", "end");
    y += 25;

    detailsGroup.append("rect")
        .attr("class", "colorBlock")
        .attr("y", y - 14)
        .attr("x", SYMBOL_X)
        .attr("fill", HISPANIC_COL)
        .attr("height", "15px")
        .attr("width", "15px");
    detailsGroup.append("text")
        .attr("class", "details")
        .text("Percent Hispanic:")
        .attr("y", y)
        .attr("x", DESC_X);
    detailsGroup.append("text")
        .attr("id", "txtHispanicPerc")
        .attr("class", "details")
        .attr("y", y)
        .attr("x", VALUE_X)
        .attr("text-anchor", "end");
    y += 25;

    detailsGroup.append("rect")
        .attr("class", "colorBlock")
        .attr("y", y - 14)
        .attr("x", SYMBOL_X)
        .attr("fill", ASIAN_COL)
        .attr("height", "15px")
        .attr("width", "15px");
    detailsGroup.append("text")
        .attr("class", "details")
        .text("Percent Asian:")
        .attr("y", y)
        .attr("x", DESC_X);
    detailsGroup.append("text")
        .attr("id", "txtAsianPerc")
        .attr("class", "details")
        .attr("y", y)
        .attr("x", VALUE_X)
        .attr("text-anchor", "end");
    y += 25;

    detailsGroup.append("rect")
        .attr("class", "colorBlock")
        .attr("y", y - 14)
        .attr("x", SYMBOL_X)
        .attr("fill", OTHER_COL)
        .attr("height", "15px")
        .attr("width", "15px");
    detailsGroup.append("text")
        .attr("class", "details")
        .text("Percent other:")
        .attr("y", y)
        .attr("x", DESC_X);
    detailsGroup.append("text")
        .attr("id", "txtOtherPerc")
        .attr("class", "details")
        .attr("y", y)
        .attr("x", VALUE_X)
        .attr("text-anchor", "end");
    y += 40;

    y = TOP_PADDING + 130;
    x = LEFT_PADDING + INCOME_WIDTH + 20;

    //add hint to show when details are hidden
    svg.append("text")
        .attr("class", "hint")
        .attr("width", DETAIL_WIDTH)
        .attr("x", x)
        .attr("y", y)
        .attr("opacity", 1)
        .text("In chart at left, each box represents a group");
    y += 25;
    svg.append("text")
        .attr("class", "hint")
        .attr("width", DETAIL_WIDTH)
        .attr("x", x)
        .attr("y", y)
        .attr("opacity", 1)
        .text("of college majors. Along the x-axis, the box");
    y += 25;
    svg.append("text")
        .attr("class", "hint")
        .attr("width", DETAIL_WIDTH)
        .attr("x", x)
        .attr("y", y)
        .attr("opacity", 1)
        .text("shows the range from lower quartile to upper");
    y += 25;
    svg.append("text")
        .attr("class", "hint")
        .attr("width", DETAIL_WIDTH)
        .attr("x", x)
        .attr("y", y)
        .attr("opacity", 1)
        .text("quartile wages. The heights of the boxes are");
    y += 25;
    svg.append("text")
        .attr("class", "hint")
        .attr("width", DETAIL_WIDTH)
        .attr("x", x)
        .attr("y", y)
        .attr("opacity", 1)
        .text("proportional to the popularity of the major");
    y += 25;
    svg.append("text")
        .attr("class", "hint")
        .attr("width", DETAIL_WIDTH)
        .attr("x", x)
        .attr("y", y)
        .attr("opacity", 1)
        .text("groups.");
    y += 45;
    svg.append("text")
        .attr("class", "hint")
        .attr("width", DETAIL_WIDTH)
        .attr("x", x)
        .attr("y", y)
        .attr("opacity", 1)
        .text("The color striation of the boxes shows");
    y += 25;
    svg.append("text")
        .attr("class", "hint")
        .attr("width", DETAIL_WIDTH)
        .attr("x", x)
        .attr("y", y)
        .attr("opacity", 1)
        .text("gender or ethnic composition of the major.");
    y += 25;
    svg.append("text")
        .attr("class", "hint")
        .attr("width", DETAIL_WIDTH)
        .attr("x", x)
        .attr("y", y)
        .attr("opacity", 1)
        .text("groups.");
    y += 45;
    svg.append("text")
        .attr("class", "hint")
        .attr("width", DETAIL_WIDTH)
        .attr("x", x)
        .attr("y", y)
        .attr("opacity", 1)
        .text("Hover mouse over a box to see more details.");
    y += 25;

    /*  
     
    */
}

function drawToggleButtons() {

    // add labels above toggle buttons

    svg.append("text")
        .attr("class", "toggleHeader")
        .text("Order by")
        .attr("y", TOP_PADDING + TOGGLE_HEIGHT - 7);
    svg.append("text")
        .attr("class", "toggleHeader")
        .text("Color by")
        .attr("y", TOP_PADDING + 2 * TOGGLE_HEIGHT + 18);
    d3.selectAll(".toggleHeader")
        .attr("font-size", 15)
        .attr("x", (LEFT_PADDING + INCOME_WIDTH + 55))
        .attr("text-anchor", "front");

    // add order by toggle buttons

    var tog = svg.append("g")
        .attr("id", "sortByIncome")
        .attr("class", "toggle")
        .attr("transform", "translate(" + (LEFT_PADDING + INCOME_WIDTH + 135) + ", " + TOP_PADDING + ")")
        .on("click", function () {
            orderBars(ORDER_BY_INCOME);
        });
    tog.append("rect")
        .attr("class", "toggle");
    tog.append("text")
        .attr("class", "toggle")
        .attr("x", 0.5 * TOGGLE_WIDTH)
        .text("Wages");
    tog = svg.append("g")
        .attr("id", "sortByPop")
        .attr("class", "toggle")
        .attr("transform", "translate(" + (LEFT_PADDING + INCOME_WIDTH + TOGGLE_WIDTH + 145) + ", " + TOP_PADDING + ")")
        .on("click", function (d) {
            orderBars(ORDER_BY_POP);
        });
    tog.append("rect")
        .attr("class", "toggle")
    tog.append("text")
        .attr("class", "toggle")
        .attr("x", 0.5 * TOGGLE_WIDTH)
        .text("Popularity");

    // add color by toggle buttons

    tog = svg.append("g")
        .attr("id", "colorByGender")
        .attr("class", "toggle")
        .attr("transform", "translate(" + (LEFT_PADDING + INCOME_WIDTH + 135) + ", " + (TOP_PADDING + TOGGLE_HEIGHT + 25) + ")")
        .on("click", function () {
            colorBars(COLOR_BY_GENDER);
        });
    tog.append("rect")
        .attr("class", "toggle");
    tog.append("text")
        .attr("class", "toggle")
        .attr("x", 0.5 * TOGGLE_WIDTH)
        .text("Gender");

    tog = svg.append("g")
        .attr("id", "colorByEthnicity")
        .attr("class", "toggle")
        .attr("transform", "translate(" + (LEFT_PADDING + INCOME_WIDTH + TOGGLE_WIDTH + 145) + ", " + (TOP_PADDING + TOGGLE_HEIGHT + 25) + ")")
        .on("click", function () {
            colorBars(COLOR_BY_RACE);
        });
    tog.append("rect")
        .attr("class", "toggle");
    tog.append("text")
        .attr("class", "toggle")
        .attr("x", 0.5 * TOGGLE_WIDTH)
        .text("Ethnicity");

    // mass formatting

    d3.selectAll(".toggle")
        .attr("width", TOGGLE_WIDTH)
        .attr("height", TOGGLE_HEIGHT);
    d3.selectAll("text.toggle")
        .attr("y", TOGGLE_HEIGHT - 7)
        .attr("text-anchor", "middle")
        .attr("font-size", 14);
}

function orderBars(orderingType) {
    d3.select("#sortByIncome").attr("opacity", orderingType == ORDER_BY_INCOME ? 1 : 0.5);
    d3.select("#sortByPop").attr("opacity", orderingType == ORDER_BY_POP ? 1 : 0.5);
    wrappers
        .transition()
        .duration(1000)
        .attr("transform", function (d) { return "translate(" + LEFT_PADDING + ", " + ((TOP_PADDING + popularity_scale(orderingType == ORDER_BY_POP ? parseFloat(d.cumPopByPop) : parseFloat(d.cumPopByMedian))) + ((orderingType == ORDER_BY_POP ? d.popularityIndex : d.medianIndex) * BAR_SPACE)) + ")"; });
}

function colorBars(coloringType) {
    d3.select("#colorByGender").attr("opacity", coloringType == COLOR_BY_GENDER ? 1 : 0.5);
    d3.select("#colorByEthnicity").attr("opacity", coloringType == COLOR_BY_RACE ? 1 : 0.5);
    d3.selectAll(".genderBar")
        .transition()
        .duration(500)
        .attr("opacity", coloringType == COLOR_BY_GENDER ? 1 : 0);
    d3.selectAll(".ethnicBar")
        .transition()
        .duration(500)
        .attr("opacity", coloringType == COLOR_BY_RACE ? 1 : 0);
}

function placeAnnotations(y, data) {
    d3.select("#annotationBar")
        .attr("transform", "translate(0," + y + ")")
        .attr("opacity", 1);
    d3.select("#perc50Line")
        .attr("x1", LEFT_PADDING + income_scale(data.percentile50))
        .attr("x2", LEFT_PADDING + income_scale(data.percentile50));
    d3.select("#perc25Line")
        .attr("x1", LEFT_PADDING + income_scale(data.percentile25))
        .attr("x2", LEFT_PADDING + income_scale(data.percentile25));
    d3.select("#perc75Line")
        .attr("x1", LEFT_PADDING + income_scale(data.percentile75))
        .attr("x2", LEFT_PADDING + income_scale(data.percentile75));
    d3.select("#maleLine")
        .attr("x1", LEFT_PADDING + income_scale(data.maleMedian))
        .attr("x2", LEFT_PADDING + income_scale(data.maleMedian));
    d3.select("#femaleLine")
        .attr("x1", LEFT_PADDING + income_scale(data.femaleMedian))
        .attr("x2", LEFT_PADDING + income_scale(data.femaleMedian));
    d3.select("#perc50Sym")
        .attr("x", LEFT_PADDING + income_scale(data.percentile50));
    d3.select("#perc25Sym")
        .attr("x", LEFT_PADDING + income_scale(data.percentile25));
    d3.select("#perc75Sym")
        .attr("x", LEFT_PADDING + income_scale(data.percentile75));
    d3.select("#maleSym")
        .attr("x", LEFT_PADDING + income_scale(data.maleMedian))
        .attr("stroke-opacity", "1");
    d3.select("#femaleSym")
        .attr("x", LEFT_PADDING + income_scale(data.femaleMedian))
        .attr("stroke-opacity", "1");
}

var percFormat = d3.format("%");

function showDetails(data) {
    d3.select("#txtMajorArea").text(data.majorGroup);

    d3.select("#txtPopularity").text(percFormat(data.popularity));

    d3.select("#txt25Perc").text(moneyFormat(data.percentile25));
    d3.select("#txt50Perc").text(moneyFormat(data.percentile50));
    d3.select("#txt75Perc").text(moneyFormat(data.percentile75));

    d3.select("#txtMaleWages").text(moneyFormat(data.maleMedian));
    d3.select("#txtFemaleWages").text(moneyFormat(data.femaleMedian));

    d3.select("#txtMalePerc").text(percFormat(1 - data.percentFemale));
    d3.select("#txtFemalePerc").text(percFormat(data.percentFemale));

    d3.select("#txtWhitePerc").text(percFormat(data.percentWhite));
    d3.select("#txtAfrAmPerc").text(percFormat(data.percentAfrAm));
    d3.select("#txtHispanicPerc").text(percFormat(data.percentHispanic));
    d3.select("#txtAsianPerc").text(percFormat(data.percentAsian));
    d3.select("#txtOtherPerc").text(percFormat(data.percentOther));
}

function focus(id) {
    groups.each(function (d) {
        if (d.popularityIndex != id)
            d3.select("#major" + d.popularityIndex)
            .attr("opacity", 0.5);
    });
    d3.select("#detailsGroup").attr("opacity", 1);
    d3.selectAll("text.hint").attr("opacity", 0);
}

function restoreAll() {
    groups.each(function (d) {
        var myG = d3.select("#major" + d.popularityIndex);
        myG.attr("opacity", 1);
    });
    d3.select("#annotationBar")
        .attr("opacity", 0);
    d3.select("#detailsGroup").attr("opacity", 0);
    d3.selectAll("text.hint").attr("opacity", 1);
}

function moneyFormat(amount) {
    return amount + "k"
}

function parseYLocation(transform) {
    //for Chrome
    if (transform.indexOf(",") >= 0)
        return parseInt(transform.substr(transform.indexOf(",") + 1, transform.indexOf(")")));
        //for IE
    else
        return parseInt(transform.substr(transform.indexOf(" ") + 1, transform.indexOf(")")));
}