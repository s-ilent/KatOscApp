# Avatar Text OSC App for VRChat
# Copyright (C) 2022 KillFrenzy / Evan Tran

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.


from threading import Timer
from pythonosc import udp_client, osc_server, dispatcher
import math, asyncio, threading
from unicodedata import normalize


class KatOscConfig:
	def __init__(self):
		self.osc_ip = "127.0.0.1" # OSC network IP
		self.osc_port = 9000 # OSC network port for sending messages

		self.osc_enable_server = True # Used to improve sync with in-game avatar and autodetect sync parameter count used for the avatar.
		self.osc_server_ip = "127.0.0.1" # OSC server IP to listen too
		self.osc_server_port = 9001 # OSC network port for recieving messages

		self.osc_delay = 0.25 # Delay between network updates in seconds. Setting this too low will cause issues.
		self.sync_params = 4 # Default sync parameters. This is automatically updated if the OSC server is enabled.

		self.line_length = 32 # Characters per line of text
		self.line_count = 4 # Maximum lines of text


class KatOsc:
	def __init__(self, config: KatOscConfig = KatOscConfig()):
		self.osc_ip = config.osc_ip
		self.osc_port = config.osc_port

		self.osc_enable_server = config.osc_enable_server
		self.osc_server_ip = config.osc_server_ip
		self.osc_server_port = config.osc_server_port

		self.osc_delay = config.osc_delay
		self.sync_params = config.sync_params

		self.line_length = config.line_length
		self.line_count = config.line_count

		self.text_length = 128 # Maximum length of text
		self.sync_params_max = 16 # Maximum sync parameters
		self.sync_params_last = 4 # Last detected sync parameters

		self.pointer_count = int(self.text_length / self.sync_params)
		self.pointer_clear = 255
		self.pointer_index_resync = 0

		self.sync_params_test_char_value = 97 # Character value to use when testing sync parameters

		self.param_visible = "KAT_Visible"
		self.param_pointer = "KAT_Pointer"
		self.param_sync = "KAT_CharSync"

		self.osc_parameter_prefix = "/avatar/parameters/"
		self.osc_avatar_change_path = "/avatar/change"
		self.osc_text = ""
		self.target_text = ""

		self.invalid_char = "?" # character used to replace invalid characters

		self.keys = {
			" ": 0,
			"!": 1,
			"\"": 2,
			"#": 3,
			"$": 4,
			"%": 5,
			"&": 6,
			"'": 7,
			"(": 8,
			")": 9,
			"*": 10,
			"+": 11,
			",": 12,
			"-": 13,
			".": 14,
			"/": 15,
			"0": 16,
			"1": 17,
			"2": 18,
			"3": 19,
			"4": 20,
			"5": 21,
			"6": 22,
			"7": 23,
			"8": 24,
			"9": 25,
			":": 26,
			";": 27,
			"<": 28,
			"=": 29,
			">": 30,
			"?": 31,
			"@": 32,
			"A": 33,
			"B": 34,
			"C": 35,
			"D": 36,
			"E": 37,
			"F": 38,
			"G": 39,
			"H": 40,
			"I": 41,
			"J": 42,
			"K": 43,
			"L": 44,
			"M": 45,
			"N": 46,
			"O": 47,
			"P": 48,
			"Q": 49,
			"R": 50,
			"S": 51,
			"T": 52,
			"U": 53,
			"V": 54,
			"W": 55,
			"X": 56,
			"Y": 57,
			"Z": 58,
			"[": 59,
			"\\": 60,
			"]": 61,
			"^": 62,
			"_": 63,
			"`": 64,
			"a": 65,
			"b": 66,
			"c": 67,
			"d": 68,
			"e": 69,
			"f": 70,
			"g": 71,
			"h": 72,
			"i": 73,
			"j": 74,
			"k": 75,
			"l": 76,
			"m": 77,
			"n": 78,
			"o": 79,
			"p": 80,
			"q": 81,
			"r": 82,
			"s": 83,
			"t": 84,
			"u": 85,
			"v": 86,
			"w": 87,
			"x": 88,
			"y": 89,
			"z": 90,
			"{": 91,
			"|": 92,
			"}": 93,
			"~": 94,
			"€": 95,
			"ぬ": 127,
			"ふ": 129,
			"あ": 130,
			"う": 131,
			"え": 132,
			"お": 133,
			"や": 134,
			"ゆ": 135,
			"よ": 136,
			"わ": 137,
			"を": 138,
			"ほ": 139,
			"へ": 140,
			"た": 141,
			"て": 142,
			"い": 143,
			"す": 144,
			"か": 145,
			"ん": 146,
			"な": 147,
			"に": 148,
			"ら": 149,
			"せ": 150,
			"ち": 151,
			"と": 152,
			"し": 153,
			"は": 154,
			"き": 155,
			"く": 156,
			"ま": 157,
			"の": 158,
			"り": 159,
			"れ": 160,
			"け": 161,
			"む": 162,
			"つ": 163,
			"さ": 164,
			"そ": 165,
			"ひ": 166,
			"こ": 167,
			"み": 168,
			"も": 169,
			"ね": 170,
			"る": 171,
			"め": 172,
			"ろ": 173,
			"。": 174,
			"ぶ": 175,
			"ぷ": 176,
			"ぼ": 177,
			"ぽ": 178,
			"べ": 179,
			"ぺ": 180,
			"だ": 181,
			"で": 182,
			"ず": 183,
			"が": 184,
			"ぜ": 185,
			"ぢ": 186,
			"ど": 187,
			"じ": 188,
			"ば": 189,
			"ぱ": 190,
			"ぎ": 191,
			"ぐ": 192,
			"げ": 193,
			"づ": 194,
			"ざ": 195,
			"ぞ": 196,
			"び": 197,
			"ぴ": 198,
			"ご": 199,
			"ぁ": 200,
			"ぃ": 201,
			"ぅ": 202,
			"ぇ": 203,
			"ぉ": 204,
			"ゃ": 205,
			"ゅ": 206,
			"ょ": 207,
			"ヌ": 208,
			"フ": 209,
			"ア": 210,
			"ウ": 211,
			"エ": 212,
			"オ": 213,
			"ヤ": 214,
			"ユ": 215,
			"ヨ": 216,
			"ワ": 217,
			"ヲ": 218,
			"ホ": 219,
			"ヘ": 220,
			"タ": 221,
			"テ": 222,
			"イ": 223,
			"ス": 224,
			"カ": 225,
			"ン": 226,
			"ナ": 227,
			"ニ": 228,
			"ラ": 229,
			"セ": 230,
			"チ": 231,
			"ト": 232,
			"シ": 233,
			"ハ": 234,
			"キ": 235,
			"ク": 236,
			"マ": 237,
			"ノ": 238,
			"リ": 239,
			"レ": 240,
			"ケ": 241,
			"ム": 242,
			"ツ": 243,
			"サ": 244,
			"ソ": 245,
			"ヒ": 246,
			"コ": 247,
			"ミ": 248,
			"モ": 249,
			"ネ": 250,
			"ル": 251,
			"メ": 252,
			"ロ": 253,
			"〝": 254,
			"°": 255
		}

		self.auto_replace_char = {
			# Full width punctuation
			"－" : "-",
			# Katakana that doesn't fit into the main table
			"ガ" : "カ〝",
			"ギ" : "キ〝",
			"グ" : "ク〝",
			"ゲ" : "ケ〝",
			"ゴ" : "コ〝",
			"ザ" : "サ〝",
			"ジ" : "シ〝",
			"ズ" : "ス〝",
			"ゼ" : "セ〝",
			"ゾ" : "ソ〝",
			"ダ" : "タ〝",
			"ヂ" : "チ〝",
			"ヅ" : "ツ〝",
			"デ" : "テ〝",
			"ド" : "ト〝",
			# These should be added to the main table later
			"ャ" : "ヤ",
			"ュ" : "ユ",
			"ョ" : "ヨ",
		}

		# Character to use in place of unknown characters
		self.invalid_char_value = self.keys.get(self.invalid_char, 0)

		# --------------
		# OSC Setup
		# --------------

		# Setup OSC Client
		self.osc_client = udp_client.SimpleUDPClient(self.osc_ip, self.osc_port)
		self.osc_timer = RepeatedTimer(self.osc_delay, self.osc_timer_loop)

		self.osc_client.send_message(self.osc_parameter_prefix + self.param_visible, True) # Make KAT visible
		self.osc_client.send_message(self.osc_parameter_prefix + self.param_pointer, 255) # Clear KAT text
		for value in range(self.sync_params):
			self.osc_client.send_message(self.osc_parameter_prefix + self.param_sync + str(value), 0.0) # Reset KAT characters sync

		# Setup OSC Server
		if self.osc_enable_server:
			try:
				self.osc_server_test_step = 1

				self.osc_dispatcher = dispatcher.Dispatcher()
				self.osc_dispatcher.map(self.osc_parameter_prefix + self.param_sync + "*", self.osc_server_handler_char)
				self.osc_dispatcher.map(self.osc_avatar_change_path + "*", self.osc_server_handler_avatar)

				self.osc_server = osc_server.ThreadingOSCUDPServer((self.osc_server_ip, self.osc_server_port), self.osc_dispatcher, asyncio.get_event_loop())
				threading.Thread(target = self.osc_server_start, daemon = True).start()
			except:
				self.osc_enable_server = False
				self.osc_server_test_step = 0

		# Start timer loop
		self.osc_timer.start()


	# Set the text to any value
	def set_text(self, text: str):
		text = normalize('NFKC', text)
		self.target_text = text

	# Syncronisation loop
	def osc_timer_loop(self):
		gui_text = self.target_text
		gui_text = normalize('NFKC', gui_text)

		fixed_text = ""
		for char in gui_text:
			replace = self.auto_replace_char.get(char)
			if replace is not None:
				fixed_text += replace
			else:
				fixed_text += char

		gui_text = fixed_text

		# Test parameter count if an update is requried
		if self.osc_enable_server:
			if self.osc_server_test_step > 0:
				# Keep text cleared during test
				self.osc_client.send_message(self.osc_parameter_prefix + self.param_pointer, self.pointer_clear)

				if self.osc_server_test_step == 1:
					# Reset sync parameters count
					self.sync_params = 0

					# Reset character text values
					for char_index in range(self.sync_params_max):
						self.osc_client.send_message(self.osc_parameter_prefix + self.param_sync + str(char_index), 0.0)
					self.osc_server_test_step = 2
					return

				elif self.osc_server_test_step == 2:
					# Set characters to test value
					for char_index in range(self.sync_params_max):
						self.osc_client.send_message(self.osc_parameter_prefix + self.param_sync + str(char_index), self.sync_params_test_char_value / 127.0)
					self.osc_server_test_step = 3
					return

				elif self.osc_server_test_step == 3:
					# Set characters back to 0
					for char_index in range(self.sync_params_max):
						self.osc_client.send_message(self.osc_parameter_prefix + self.param_sync + str(char_index), 0.0)
					self.osc_server_test_step = 4
					return

				elif self.osc_server_test_step == 4:
					# Finish the parameter sync test
					if self.sync_params == 0:
						self.sync_params = self.sync_params_last # Test failed, reuse last detected param count
					else:
						self.sync_params_last = self.sync_params
					self.pointer_count = int(self.text_length / self.sync_params)
					self.osc_server_test_step = 0
					self.osc_text = " ".ljust(self.text_length) # Resync letters

		# Do not process anything if sync parameters are not setup
		if self.sync_params == 0:
			return

		# Sends clear text message if all text is empty
		if gui_text.strip("\n").strip(" ") == "":
			self.osc_client.send_message(self.osc_parameter_prefix + self.param_pointer, self.pointer_clear)
			self.osc_text = " ".ljust(self.text_length)
			return

		# Make sure KAT is visible even after avatar change
		self.osc_client.send_message(self.osc_parameter_prefix + self.param_visible, True)

		# Pad line feeds with spaces for OSC
		text_lines = gui_text.split("\n")
		for index, text in enumerate(text_lines):
			text_lines[index] = self._pad_line(text)
		gui_text = self._list_to_string(text_lines)

		# Pad text with spaces up to the text limit
		gui_text = gui_text.ljust(self.text_length)
		osc_text = self.osc_text.ljust(self.text_length)

		# Text syncing
		if gui_text != self.osc_text: # GUI text is different, needs sync
			osc_chars = list(osc_text)

			for pointer_index in range(self.pointer_count):
				# Check if characters within this pointer are different
				equal = True
				for char_index in range(self.sync_params):
					index = (pointer_index * self.sync_params) + char_index

					if gui_text[index] != osc_text[index]:
						equal = False
						break

				if equal == False: # Characters not equal, need to sync this pointer position
					self.osc_update_pointer(pointer_index, gui_text, osc_chars)
					return

		# No updates required, use time to resync text
		self.pointer_index_resync = self.pointer_index_resync + 1
		if self.pointer_index_resync >= self.pointer_count:
			self.pointer_index_resync = 0

		pointer_index = self.pointer_index_resync
		self.osc_update_pointer(pointer_index, gui_text, osc_chars)


	# Starts the OSC server
	def osc_server_start(self):
		self.osc_server.serve_forever(2)


	# Handle OSC server to detect the correct sync parameters to use
	def osc_server_handler_char(self, address, value, *args):
		if self.osc_server_test_step > 0:
			length = len(self.osc_parameter_prefix + self.param_sync)
			self.sync_params = max(self.sync_params, int(address[length:]) + 1)


	# Handle OSC server to retest sync on avatar change
	def osc_server_handler_avatar(self, address, value, *args):
		self.osc_server_test_step = 1


	# Updates the characters within a pointer
	def osc_update_pointer(self, pointer_index, gui_text, osc_chars):
		self.osc_client.send_message(self.osc_parameter_prefix + self.param_pointer, pointer_index + 1) # Set pointer position

		# Loop through characters within this pointer and set them
		for char_index in range(self.sync_params):
			index = (pointer_index * self.sync_params) + char_index
			gui_char = gui_text[index]

			# Convert character to the key value, replace invalid characters
			key = self.keys.get(gui_char, self.invalid_char_value)

			# Calculate character float value for OSC
			value = float(key)
			if value > 127.5:
				value = value - 256.0
			value = value / 127.0

			self.osc_client.send_message(self.osc_parameter_prefix + self.param_sync + str(char_index), value)
			osc_chars[index] = gui_char # Apply changes to the networked value

		self.osc_text = self._list_to_string(osc_chars)


	# Combines an array of strings into a single string
	def _list_to_string(self, string: str):
		return "".join(string)


	# Pads the text line to its effective length
	def _pad_line(self, text: str):
		return text.ljust(self._get_padded_length(text))


	# Gets the effective padded length of a line
	def _get_padded_length(self, text: str):
		lines = max(math.ceil(len(text) / self.line_length), 1)
		return self.line_length * lines


	# Stop the timer and hide the text overlay
	def stop(self):
		self.osc_timer.stop()
		self.hide()


	# Restart the timer for syncing texts and show the overlay
	def start(self):
		self.osc_timer.start()
		self.show()


	# show overlay
	def show(self):
		self.osc_client.send_message(self.osc_parameter_prefix + self.param_visible, True) # Hide KAT


	# hide overlay
	def hide(self):
		self.osc_client.send_message(self.osc_parameter_prefix + self.param_visible, False) # Hide KAT



class RepeatedTimer(object):
	def __init__(self, interval, function, *args, **kwargs):
		self._timer     = None
		self.interval   = interval
		self.function   = function
		self.args       = args
		self.kwargs     = kwargs
		self.is_running = False
		self.start()

	def _run(self):
		self.is_running = False
		self.start()
		self.function(*self.args, **self.kwargs)

	def start(self):
		if not self.is_running:
			self._timer = Timer(self.interval, self._run)
			self._timer.start()
			self.is_running = True

	def stop(self):
		self._timer.cancel()
		self.is_running = False

