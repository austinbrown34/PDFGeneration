# PDFServer

PDFServer allows for flexible, dynamic, and rapid PDF generation!

- Built to leverage Adobe DC Pro, extend it's capabilities, but not depend on it.

- Makes it easy to define a job, it's templates, template rules, and custom scripts.

- Simply define a job, post some data to the PDFServer API, and receive a generated PDF.

Runs on AWS Lambda * Able to run multiple jobs concurrently * S3 template hosting.

## Current Features:

- Template Rules Configuration

- Job Specific Plugin Creation

- Fill PDF Form Fields

- Create Placeholder Images (...to represent where dynamic images go)

- Add Dynamic Visualization Elements (...make use of HTML5, CSS3, and JS to create DataTables, Sparklines, and so much more)

- PDF Delivery Options

- Easy S3 Integration

* Plus A Full Arsenal of PDF Tools (...each tool able to be used individually)

## Tools Include:

- Get Form Fields From PDF

- Create FDF File

- Merge FDF & PDF --> Flattened/Filled PDF Form

- Get Placeholder Tag Values

- Set Placeholder Tag Values

- Extract Images From PDF

- Get PDF XML Structure, PDF Image Info (coords, width, height, etc.), & PDF Text

- Remove Images From PDF

- Repair PDF

- Create PDF Data Visualizations From HTML5/CSS3/JS

- Add Images To PDF

- Add Visualizations To PDF

- Merge PDFs


## Installation

1. Clone the PDFServer repository: 'git clone https://github.com/ConfidentCannabis/PDFServer.git'

2. Create a Virtual Environment: 'virtualenv env'

3. Install Requirements: 'pip install -r requirements.txt'

4. Make sure your AWS Credentials are configured and saved: ~/.aws/credentials

5. If it's your first time deploying: 'zappa deploy production' - else - 'zappa update production'


## Usage

TODO: Write usage instructions

## Contributing

1. Fork it!
2. Create your feature branch: `git checkout -b my-new-feature`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin my-new-feature`
5. Submit a pull request :D

## History

TODO: Write history

## Credits

TODO: Write credits

## License

TODO: Write license
