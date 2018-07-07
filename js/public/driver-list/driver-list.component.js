angular
    .module('driverList')
    .component("driverList", {
        templateUrl: "driver-list/driver-list.template.html",
        controller: function DriversController($http) {
            var self = this;
            $http.get('driversDescribe.json').then(function (driverProfile) {
                driversDict = {};
                for (did in driverProfile.data) {
                    getColor(driverProfile.data[did]);
                    driversDict[did] = driverProfile.data[did];
                }

                $http.get('predictions.json').then(function (driverRes) {
                    //console.log(driversDict);
                    for (did in driverRes.data) {
                        driversDict[did].predictions = driverRes.data[did];
                    }

                    driversArray = [];
                    for (did in driversDict) {
                        driversArray.push([did, driversDict[did]]);
                    }
                    driversArray.sort(function (a, b) {
                        if (a[1].constructor < b[1].constructor) {
                            return -1;
                        }
                        else if (a[1].constructor > b[1].constructor) {
                            return 1;
                        }
                        else return 0;
                    });
                    self.drivers = driversArray;
                });
            });
            this.rowClicked = function (driver) {
                d3.select("#selectedDriver")
                    .text(driver.name)
                    .style("color", driver.color);
                //console.log(driver);
                changeData(driver);
            }
        }
    });

function getColor(driver) {
    if (driver.constructor === "Mercedes") {
        driver.color = "#00d2be";
    }
    else if (driver.constructor === "Ferrari") {
        driver.color = "#dc0000";
    }
    else if (driver.constructor === "Red Bull") {
        driver.color = "#00327d";
    }
    else if (driver.constructor === "Force India") {
        driver.color = "#f596c8";
    }
    else if (driver.constructor === "Williams") {
        driver.color = "#ffffff";
    }
    else if (driver.constructor === "Renault") {
        driver.color = "#fff500";
    }
    else if (driver.constructor === "Toro Rosso") {
        driver.color = "#0032ff";
    }
    else if (driver.constructor === "Haas F1 Team") {
        driver.color = "#5a5a5a";
    }
    else if (driver.constructor === "McLaren") {
        driver.color = "#ff8700";
    }
    else if (driver.constructor === "Sauber") {
        driver.color = "#9b0000";
    }
    else {
        //console.log(driver.constructor);
        throw Error();
    }
}