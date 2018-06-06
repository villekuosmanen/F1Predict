const http = require('http');
var express = require('express');
var app = express();
const port = 3000;

app.listen(port);
app.use(express.static('public'));
//app.get("/", serveStatic);  //Default one

//function serveStatic(req, res) {
    //res.sendFile("predictions.json", { root: '.' });
//}