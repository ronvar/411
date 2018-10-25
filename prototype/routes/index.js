const express = require('express');
const router = express.Router();

const request = require('request')

/* API KEYS */
const AzureAPIKey = require('../auth.json').AzureAPIKey;

/* GET home page. */

router.get('/', function(req, res, next) {
    var options = { method: 'POST',
        url: 'https://westus.api.cognitive.microsoft.com/face/v1.0/detect',
        qs: { returnFaceAttributes: 'emotion' },
        headers:
            { 'Postman-Token': '0e90a4db-760f-48c7-baa4-8f3004da3b35',
                'cache-control': 'no-cache',
                'Content-Type': 'application/json',
                'Ocp-Apim-Subscription-Key': AzureAPIKey },
        body: { url: 'https://img.purch.com/h/1000/aHR0cDovL3d3dy5saXZlc2NpZW5jZS5jb20vaW1hZ2VzL2kvMDAwLzA2OS85MDcvb3JpZ2luYWwvYW5ncnktZmFjZS5qcGVn' },
        json: true
    };
    request(options, function (error, response, body) {
        if (error) throw new Error(error);
        var emotions = body[0].faceAttributes.emotion;
        console.log(body[0].faceAttributes.emotion);
        res.render('index', emotions);
    });
});



module.exports = router;

router.use('/', router);
