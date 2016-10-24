process.argv.forEach(function (val, index, array) {
  console.log(index + ': ' + val);
});

generator = require('/tmp/fdf/lib/generator.js').generator;
generator(process.argv[2], process.argv[3]);
