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
            {
                'cache-control': 'no-cache',
                'Content-Type': 'application/json',
                'Ocp-Apim-Subscription-Key': AzureAPIKey },
        body: { url: 'https://pbs.twimg.com/profile_images/1034484319866302472/O8nhACsb_400x400.jpg' },
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
