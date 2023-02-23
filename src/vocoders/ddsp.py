import os
import librosa
import torch

from modules.ddsp.vocoder import load_model, Audio2Mel
from src.vocoders.base_vocoder import BaseVocoder, register_vocoder
from utils.hparams import hparams


@register_vocoder
class DDSP(BaseVocoder):
    def __init__(self, device=None):
        if device is None:
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.device = device
        model_path = hparams['vocoder_ckpt']
        assert os.path.exists(model_path), 'DDSP model file is not found!'
        self.model, self.args = load_model(model_path, device=self.device)

    def spec2wav_torch(self, mel, f0):  # mel: [B, T, bins] f0: [B, T]
        if self.args.data.sampling_rate != hparams['audio_sample_rate']:
            print('Mismatch parameters: hparams[\'audio_sample_rate\']=', hparams['audio_sample_rate'], '!=',
                  self.args.data.sampling_rate, '(vocoder)')
        if self.args.data.n_mels != hparams['audio_num_mel_bins']:
            print('Mismatch parameters: hparams[\'audio_num_mel_bins\']=', hparams['audio_num_mel_bins'], '!=',
                  self.args.data.n_mels, '(vocoder)')
        if self.args.data.n_fft != hparams['fft_size']:
            print('Mismatch parameters: hparams[\'fft_size\']=', hparams['fft_size'], '!=', self.args.data.n_fft, '(vocoder)')
        if self.args.data.win_length != hparams['win_size']:
            print('Mismatch parameters: hparams[\'win_size\']=', hparams['win_size'], '!=', self.args.data.win_length,
                  '(vocoder)')
        if self.args.data.block_size != hparams['hop_size']:
            print('Mismatch parameters: hparams[\'hop_size\']=', hparams['hop_size'], '!=', self.args.data.block_size,
                  '(vocoder)')
        if self.args.data.mel_fmin != hparams['fmin']:
            print('Mismatch parameters: hparams[\'fmin\']=', hparams['fmin'], '!=', self.args.data.mel_fmin, '(vocoder)')
        if self.args.data.mel_fmax != hparams['fmax']:
            print('Mismatch parameters: hparams[\'fmax\']=', hparams['fmax'], '!=', self.args.data.mel_fmax, '(vocoder)')
        with torch.no_grad():
            f0 = f0.unsqueeze(-1)
            signal, _, (s_h, s_n) = self.model(mel, f0, max_upsample_dim = self.args.train.max_upsample_dim)
            signal = signal.view(-1)
        return signal

    def spec2wav(self, mel, f0):
        if self.args.data.sampling_rate != hparams['audio_sample_rate']:
            print('Mismatch parameters: hparams[\'audio_sample_rate\']=', hparams['audio_sample_rate'], '!=',
                  self.args.data.sampling_rate, '(vocoder)')
        if self.args.data.n_mels != hparams['audio_num_mel_bins']:
            print('Mismatch parameters: hparams[\'audio_num_mel_bins\']=', hparams['audio_num_mel_bins'], '!=',
                  self.args.data.n_mels, '(vocoder)')
        if self.args.data.n_fft != hparams['fft_size']:
            print('Mismatch parameters: hparams[\'fft_size\']=', hparams['fft_size'], '!=', self.args.data.n_fft, '(vocoder)')
        if self.args.data.win_length != hparams['win_size']:
            print('Mismatch parameters: hparams[\'win_size\']=', hparams['win_size'], '!=', self.args.data.win_length,
                  '(vocoder)')
        if self.args.data.block_size != hparams['hop_size']:
            print('Mismatch parameters: hparams[\'hop_size\']=', hparams['hop_size'], '!=', self.args.data.block_size,
                  '(vocoder)')
        if self.args.data.mel_fmin != hparams['fmin']:
            print('Mismatch parameters: hparams[\'fmin\']=', hparams['fmin'], '!=', self.args.data.mel_fmin, '(vocoder)')
        if self.args.data.mel_fmax != hparams['fmax']:
            print('Mismatch parameters: hparams[\'fmax\']=', hparams['fmax'], '!=', self.args.data.mel_fmax, '(vocoder)')
        with torch.no_grad():
            mel = torch.FloatTensor(mel).unsqueeze(0).to(self.device)
            f0 = torch.FloatTensor(f0).unsqueeze(0).unsqueeze(-1).to(self.device)
            signal, _, (s_h, s_n) = self.model(mel, f0, max_upsample_dim = self.args.train.max_upsample_dim)
            signal = signal.view(-1)
        wav_out = signal.cpu().numpy()
        return wav_out

    @staticmethod
    def wav2spec(inp_path, keyshift=0, speed=1, device=None):
        if device is None:
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
        sampling_rate = hparams['audio_sample_rate']
        n_mel_channels = hparams['audio_num_mel_bins']
        n_fft = hparams['fft_size']
        win_length = hparams['win_size']
        hop_length = hparams['hop_size']
        mel_fmin = hparams['fmin']
        mel_fmax = hparams['fmax']
        
        # load input
        x, _ = librosa.load(inp_path, sr=sampling_rate)
        x_t = torch.from_numpy(x).float().to(device)
        x_t = x_t.unsqueeze(0).unsqueeze(0) # (T,) --> (1, 1, T)
        
        # mel analysis
        mel_extractor = Audio2Mel(
            hop_length=hop_length,
            sampling_rate=sampling_rate,
            n_mel_channels=n_mel_channels,
            win_length=win_length,
            n_fft=n_fft,
            mel_fmin=mel_fmin,
            mel_fmax=mel_fmax).to(device)
    
        mel = mel_extractor(x_t, keyshift=keyshift, speed=speed)
    
        return x, mel.squeeze(0).cpu().numpy()
