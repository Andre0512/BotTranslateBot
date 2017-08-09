const translate = require('google-translate-api');

translate(process.argv[4], {from: process.argv[2], to: process.argv[3]}).then(res => {
    console.log(res.text);
}).catch(err => {
    console.error(err);
});
