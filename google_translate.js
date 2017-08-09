const translate = require('google-translate-api');

translate(process.argv[3], {from: process.argv[1], to: process.argv[2]}).then(res => {
    console.log(res);
}).catch(err => {
    console.error(err);
});
