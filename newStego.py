from flask import Flask, render_template, request, redirect, send_file, flash
import wave
import os
from werkzeug.utils import secure_filename
import math
from bit_manipulation import lsb_deinterleave_bytes, lsb_interleave_bytes

UPLOAD_FOLDER = 'files/'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

#route to main page
@app.route('/')
def main():
    return render_template('main.html')

#route to encoding page
@app.route('/encode', methods=['GET', 'POST'])
def encode():
    if request.method == 'POST':
        f = request.files['audiofile']
        coverAudio = secure_filename(f.filename)
        f.save(os.path.join(app.config['UPLOAD_FOLDER'], coverAudio))

        secfile = request.files['secretfile']
        secretFile = secure_filename(secfile.filename)
        secfile.save(os.path.join(app.config['UPLOAD_FOLDER'], secretFile))

        lsbnum = request.form['lsbnum']
        num_lsb = int(lsbnum)

        if coverAudio is None:
            flash("Sound file path is required")
        if secretFile is None:
            flash("A secret file path is required")
        
        # get the cover audio parameters
        audio = wave.open(UPLOAD_FOLDER+coverAudio, mode="rb")
        params = audio.getparams()
        num_channels = audio.getnchannels()
        sample_width = audio.getsampwidth()
        num_frames = audio.getnframes()
        num_samples = num_frames * num_channels

        # We can hide up to num_lsb bits in each sample of the sound file
        max_bytes_to_hide = (num_samples * num_lsb) // 8
        file_size = os.stat(UPLOAD_FOLDER+secretFile).st_size

        sound_frames = audio.readframes(num_frames) #read the audio
        # read the content of the data file to be hidden
        with open(UPLOAD_FOLDER+secretFile, "rb") as file:
            data = file.read()

        if file_size > max_bytes_to_hide:
            required_lsb = math.ceil(file_size * 8 / num_samples)
            msg = str("Input file too large to hide, "f"requires {required_lsb} LSBs, using {num_lsb}")
            flash(msg)

        if sample_width != 1 and sample_width != 2:
            # Python's wave module doesn't support higher sample widths
            flash("File has an unsupported bit-depth")

        sound_frames = lsb_interleave_bytes(sound_frames, data, num_lsb, byte_depth=sample_width)

        newAudio = 'stegoAudio.wav'
        sound_steg = wave.open(newAudio, "w")
        sound_steg.setparams(params)
        sound_steg.writeframes(sound_frames)
        sound_steg.close()
        str_filesize = str(file_size)
        str_maxbytes = str(max_bytes_to_hide)
        audio.close()
        return redirect ('/downloadfile/'+newAudio+'/'+str_filesize+'/'+lsbnum+'/'+str_maxbytes)
    return render_template('encode.html')

#route to the download page
@app.route("/downloadfile/<filename>/<filesize>/<lsbnum>/<maxbytes>", methods = ['GET'])
def download_file(filename, filesize, lsbnum, maxbytes):
    return render_template('download.html',value=filename, value1=filesize, value2=lsbnum, value3=maxbytes)

#to download the resulting stego audio
@app.route('/return-files/<filename>')
def return_files_tut(filename):
    file_path = filename
    return send_file(file_path, as_attachment=True, attachment_filename='')

#route to decoding page
@app.route('/decode', methods=['GET', 'POST'])
def decode():
    if request.method == 'POST':
        f = request.files['audiofile']
        stegoAudio = secure_filename(f.filename)
        f.save(os.path.join(app.config['UPLOAD_FOLDER'], stegoAudio))

        lsbnum = request.form['numlsb']
        num_lsb = int(lsbnum)
        bytesnum = request.form['numbytes']
        bytes_to_recover = int(bytesnum)

        if stegoAudio is None:
            flash("An input sound file path is required")
        if bytesnum is None:
            flash("The number of bytes to recover is required")

        # get the stego audio parameters
        audio = wave.open(UPLOAD_FOLDER+stegoAudio, mode='rb')
        sample_width = audio.getsampwidth()
        num_frames = audio.getnframes()
        sound_frames = audio.readframes(num_frames)

        if sample_width != 1 and sample_width != 2:
            # Python's wave module doesn't support higher sample widths
            flash("File has an unsupported bit-depth")

        data = lsb_deinterleave_bytes(sound_frames, 8 * bytes_to_recover, num_lsb, byte_depth=sample_width)

        decoded = data.decode('utf-8', 'ignore')
        audio.close()
        return render_template('display.html', value=decoded, value1=bytes_to_recover)
    return render_template('decode.html')

if __name__ == "__main__":
    app.run(debug=True)