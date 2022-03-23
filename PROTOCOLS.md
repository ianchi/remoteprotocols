## List of supported protocols

| Protocol | Signature | Type | Description |
| --- | --- | --- | --- |
| [broadlink](#broadlink) | broadlink:&lt;b64&gt;:&lt;frequency?=0&gt; | raw | Broadlink base64 raw format |
| [coolix](#coolix) | coolix:&lt;data&gt; | IR | Coolix 24-bit IR code |
| [dish](#dish) | dish:&lt;command&gt;:&lt;receiver?=1&gt; | IR | Dish Network IR code |
| [duration](#duration) | duration:&lt;durations&gt;:&lt;frequency?=0&gt; | raw | Raw durations format |
| [jvc](#jvc) | jvc:&lt;data&gt; | IR | JVC IR code |
| [lg](#lg) | lg:&lt;data&gt;:&lt;nbits?=28&gt; | IR | LG IR code |
| [midea](#midea) | midea:&lt;code&gt; | IR | Midea 48-bit IR code. 8-bit checksum added automatically |
| [miio](#miio) | miio:&lt;b64&gt;:&lt;frequency?=38400&gt; | raw | Miio base64 raw format |
| [nec](#nec) | nec:&lt;address&gt;:&lt;command&gt; | IR | NEC IR code (in LSB form) |
| [nexa](#nexa) | nexa:&lt;device&gt;:&lt;group&gt;:&lt;state&gt;:&lt;channel&gt;:&lt;level&gt; | RF | Nexa RF code |
| [panasonic](#panasonic) | panasonic:&lt;address&gt;:&lt;command&gt; | IR | Panasonic IR code |
| [pioneer](#pioneer) | pioneer:&lt;rc_code_1&gt;:&lt;rc_code_2?=0&gt; | IR | Pioneer IR code |
| [pronto](#pronto) | pronto:&lt;data&gt;:&lt;frequency?=0&gt; | raw | Pronto hex raw format |
| [rc5](#rc5) | rc5:&lt;address&gt;:&lt;command&gt; | IR | RC5 IR code |
| [rc_switch](#rc_switch) | rc_switch:&lt;data&gt;:&lt;nbits&gt;:&lt;preset?=1&gt;:&lt;sync_high?=0&gt;:&lt;sync_low?=0&gt;:&lt;one_high?=0&gt;:&lt;one_low?=0&gt;:&lt;zero_high?=0&gt;:&lt;zero_low?=0&gt; | IR | RC switch data with preset |
| [rc_switch_a](#rc_switch_a) | rc_switch_a:&lt;group&gt;:&lt;device&gt;:&lt;state&gt;:&lt;preset?=1&gt;:&lt;sync_high?=0&gt;:&lt;sync_low?=0&gt;:&lt;one_high?=0&gt;:&lt;one_low?=0&gt;:&lt;zero_high?=0&gt;:&lt;zero_low?=0&gt; | IR | RC Switch Type A (10 pole DIP switch) |
| [rc_switch_b](#rc_switch_b) | rc_switch_b:&lt;address&gt;:&lt;channel&gt;:&lt;state&gt;:&lt;preset?=1&gt;:&lt;sync_high?=0&gt;:&lt;sync_low?=0&gt;:&lt;one_high?=0&gt;:&lt;one_low?=0&gt;:&lt;zero_high?=0&gt;:&lt;zero_low?=0&gt; | IR | RC Switch Type B (two rotary/sliding switches with four setting) |
| [rc_switch_c](#rc_switch_c) | rc_switch_c:&lt;family&gt;:&lt;device&gt;:&lt;group&gt;:&lt;state&gt;:&lt;preset?=1&gt;:&lt;sync_high?=0&gt;:&lt;sync_low?=0&gt;:&lt;one_high?=0&gt;:&lt;one_low?=0&gt;:&lt;zero_high?=0&gt;:&lt;zero_low?=0&gt; | IR | RC Switch Type C (Intertechno) |
| [rc_switch_d](#rc_switch_d) | rc_switch_d:&lt;group&gt;:&lt;device&gt;:&lt;state&gt;:&lt;preset&gt;:&lt;sync_high?=0&gt;:&lt;sync_low?=0&gt;:&lt;one_high?=0&gt;:&lt;one_low?=0&gt;:&lt;zero_high?=0&gt;:&lt;zero_low?=0&gt; | IR | RC Switch Type D (Status) |
| [samsung](#samsung) | samsung:&lt;address&gt;:&lt;command&gt; | IR | Samsung IR code. 32 bits |
| [samsung36](#samsung36) | samsung36:&lt;address&gt;:&lt;command&gt; | IR | Samsumg36 IR code.  It transmits the address and command in two packets separated by a “space”. |
| [sony](#sony) | sony:&lt;data&gt;:&lt;nbits?=12&gt; | IR | Sony IR code |
| [toshiba_ac](#toshiba_ac) | toshiba_ac:&lt;rc_code_1&gt;:&lt;rc_code_2?=0&gt; | IR | Toshiba AC IR code |
## Protocols details


### **broadlink**
Broadlink base64 raw format

*Type:* raw

*Signature:* broadlink:&lt;b64&gt;:&lt;frequency?=0&gt;

*Arguments:*

- *b64*: Base 64 encoded data

- *frequency*: Frequency

   optional. Default: 0


### **coolix**
Coolix 24-bit IR code

*Type:* IR

*Signature:* coolix:&lt;data&gt;

*Arguments:*

- *data*: Code to send

   range: 0-24bits


### **dish**
Dish Network IR code

*Type:* IR

*Signature:* dish:&lt;command&gt;:&lt;receiver?=1&gt;

*Arguments:*

- *command*: Command to send

   range: 0-63

- *receiver*: Receiver ID to target

   optional. Default: 1

   range: 1-16


### **duration**
Raw durations format

*Type:* raw

*Signature:* duration:&lt;durations&gt;:&lt;frequency?=0&gt;

*Arguments:*

- *durations*: List of durations (comma separated)

- *frequency*: Frequency

   optional. Default: 0


### **jvc**
JVC IR code

*Type:* IR

*Signature:* jvc:&lt;data&gt;

*Arguments:*

- *data*: JVC code to send

   range: 0-16bits


### **lg**
LG IR code

*Type:* IR

*Signature:* lg:&lt;data&gt;:&lt;nbits?=28&gt;

*Arguments:*

- *data*: LG code to send

   range: 0-32bits

- *nbits*: Number of bits to send (28 or 32)

   optional. Default: 28

   range: 0-32

   values: [28, 32]


### **midea**
Midea 48-bit IR code. 8-bit checksum added automatically

*Type:* IR

*Signature:* midea:&lt;code&gt;

*Arguments:*

- *code*: 48-bit Midea code to send as list of 5 hex/integers

   range: 0-48bits


### **miio**
Miio base64 raw format

*Type:* raw

*Signature:* miio:&lt;b64&gt;:&lt;frequency?=38400&gt;

*Arguments:*

- *b64*: Base 64 encoded data

- *frequency*: Frequency

   optional. Default: 38400


### **nec**
NEC IR code (in LSB form)

*Type:* IR

*Signature:* nec:&lt;address&gt;:&lt;command&gt;

*Arguments:*

- *address*: Address to send

   range: 0-16bits

- *command*: NEC command to send

   range: 0-16bits


### **nexa**
Nexa RF code

*Type:* RF

*Signature:* nexa:&lt;device&gt;:&lt;group&gt;:&lt;state&gt;:&lt;channel&gt;:&lt;level&gt;

*Arguments:*

- *device*: Nexa device code

   range: 0-32bits

- *group*: Nexa group code

   range: 0-1

- *state*: Nexa state code to send (0-OFF, 1-ON, 2-DIMMER LEVEL)

   range: 0-2

- *channel*: Nexa channel code

   range: 0-15

- *level*: Nexa level code

   range: 0-8bits


### **panasonic**
Panasonic IR code

*Type:* IR

*Signature:* panasonic:&lt;address&gt;:&lt;command&gt;

*Arguments:*

- *address*: Address to send

   range: 0-16bits

- *command*: NEC command to send

   range: 0-32bits


### **pioneer**
Pioneer IR code

*Type:* IR

*Signature:* pioneer:&lt;rc_code_1&gt;:&lt;rc_code_2?=0&gt;

*Arguments:*

- *rc_code_1*: Remote control code

   range: 0-16bits

- *rc_code_2*: Secondary remote control code. Some code are sent in two parts

   optional. Default: 0

   range: 0-16bits


*Notes:* Pioneer devices may require that a given code is received multiple times before they will act on it.

If unable to find your specific device in the documentation,
find a device in the same class, as the codes are largely shared among devices within a given class.



*Links:*
- [https://www.pioneerelectronics.com/PUSA/Support/Home-Entertainment-Custom-Install/IR+Codes](https://www.pioneerelectronics.com/PUSA/Support/Home-Entertainment-Custom-Install/IR+Codes)

### **pronto**
Pronto hex raw format

*Type:* raw

*Signature:* pronto:&lt;data&gt;:&lt;frequency?=0&gt;

*Arguments:*

- *data*: Data in hex codes space separated

- *frequency*: Frequency

   optional. Default: 0


### **rc5**
RC5 IR code

*Type:* IR

*Signature:* rc5:&lt;address&gt;:&lt;command&gt;

*Arguments:*

- *address*: Address to send

   range: 0-31

- *command*: RC5 command to send

   range: 0-127


### **rc_switch**
RC switch data with preset

*Type:* IR

*Signature:* rc_switch:&lt;data&gt;:&lt;nbits&gt;:&lt;preset?=1&gt;:&lt;sync_high?=0&gt;:&lt;sync_low?=0&gt;:&lt;one_high?=0&gt;:&lt;one_low?=0&gt;:&lt;zero_high?=0&gt;:&lt;zero_low?=0&gt;

*Arguments:*

- *data*: Raw code to send

   range: 0-64bits

- *nbits*: Number of bits of data to transmit

   range: 1-64

- *preset*: Preset number 1-8 or 0 for custom durations

   optional. Default: 1

   range: 0-8

- *sync_high*: Sync High duration (for Preset 0)

   optional. Default: 0

   range: -2147483648-32bits

- *sync_low*: Sync Low duration (for Preset 0)

   optional. Default: 0

   range: -2147483648-32bits

- *one_high*: One High duration (for Preset 0)

   optional. Default: 0

   range: -2147483648-32bits

- *one_low*: One Low duration (for Preset 0)

   optional. Default: 0

   range: -2147483648-32bits

- *zero_high*: Zero High duration (for Preset 0)

   optional. Default: 0

   range: -2147483648-32bits

- *zero_low*: Zero Low duration (for Preset 0)

   optional. Default: 0

   range: -2147483648-32bits


### **rc_switch_a**
RC Switch Type A (10 pole DIP switch)

*Type:* IR

*Signature:* rc_switch_a:&lt;group&gt;:&lt;device&gt;:&lt;state&gt;:&lt;preset?=1&gt;:&lt;sync_high?=0&gt;:&lt;sync_low?=0&gt;:&lt;one_high?=0&gt;:&lt;one_low?=0&gt;:&lt;zero_high?=0&gt;:&lt;zero_low?=0&gt;

*Arguments:*

- *group*: Group

   range: 0-31

- *device*: Device

   range: 0-31

- *state*: State

   range: 0-1

- *preset*: Preset number 1-8 or 0 for custom durations

   optional. Default: 1

   range: 0-8

- *sync_high*: Sync High duration (for Preset 0)

   optional. Default: 0

   range: -2147483648-32bits

- *sync_low*: Sync Low duration (for Preset 0)

   optional. Default: 0

   range: -2147483648-32bits

- *one_high*: One High duration (for Preset 0)

   optional. Default: 0

   range: -2147483648-32bits

- *one_low*: One Low duration (for Preset 0)

   optional. Default: 0

   range: -2147483648-32bits

- *zero_high*: Zero High duration (for Preset 0)

   optional. Default: 0

   range: -2147483648-32bits

- *zero_low*: Zero Low duration (for Preset 0)

   optional. Default: 0

   range: -2147483648-32bits


### **rc_switch_b**
RC Switch Type B (two rotary/sliding switches with four setting)

*Type:* IR

*Signature:* rc_switch_b:&lt;address&gt;:&lt;channel&gt;:&lt;state&gt;:&lt;preset?=1&gt;:&lt;sync_high?=0&gt;:&lt;sync_low?=0&gt;:&lt;one_high?=0&gt;:&lt;one_low?=0&gt;:&lt;zero_high?=0&gt;:&lt;zero_low?=0&gt;

*Arguments:*

- *address*: Address

   range: 1-4

- *channel*: Channel

   range: 1-4

- *state*: State

   range: 0-1

- *preset*: Preset number 1-8 or 0 for custom durations

   optional. Default: 1

   range: 0-8

- *sync_high*: Sync High duration (for Preset 0)

   optional. Default: 0

   range: -2147483648-32bits

- *sync_low*: Sync Low duration (for Preset 0)

   optional. Default: 0

   range: -2147483648-32bits

- *one_high*: One High duration (for Preset 0)

   optional. Default: 0

   range: -2147483648-32bits

- *one_low*: One Low duration (for Preset 0)

   optional. Default: 0

   range: -2147483648-32bits

- *zero_high*: Zero High duration (for Preset 0)

   optional. Default: 0

   range: -2147483648-32bits

- *zero_low*: Zero Low duration (for Preset 0)

   optional. Default: 0

   range: -2147483648-32bits


### **rc_switch_c**
RC Switch Type C (Intertechno)

*Type:* IR

*Signature:* rc_switch_c:&lt;family&gt;:&lt;device&gt;:&lt;group&gt;:&lt;state&gt;:&lt;preset?=1&gt;:&lt;sync_high?=0&gt;:&lt;sync_low?=0&gt;:&lt;one_high?=0&gt;:&lt;one_low?=0&gt;:&lt;zero_high?=0&gt;:&lt;zero_low?=0&gt;

*Arguments:*

- *family*: Family A=0 to P=15

   range: 0-15

- *device*: Device

   range: 1-4

- *group*: Group

   range: 1-4

- *state*: State

   range: 0-1

- *preset*: Preset number 1-8 or 0 for custom durations

   optional. Default: 1

   range: 0-8

- *sync_high*: Sync High duration (for Preset 0)

   optional. Default: 0

   range: -2147483648-32bits

- *sync_low*: Sync Low duration (for Preset 0)

   optional. Default: 0

   range: -2147483648-32bits

- *one_high*: One High duration (for Preset 0)

   optional. Default: 0

   range: -2147483648-32bits

- *one_low*: One Low duration (for Preset 0)

   optional. Default: 0

   range: -2147483648-32bits

- *zero_high*: Zero High duration (for Preset 0)

   optional. Default: 0

   range: -2147483648-32bits

- *zero_low*: Zero Low duration (for Preset 0)

   optional. Default: 0

   range: -2147483648-32bits


### **rc_switch_d**
RC Switch Type D (Status)

*Type:* IR

*Signature:* rc_switch_d:&lt;group&gt;:&lt;device&gt;:&lt;state&gt;:&lt;preset&gt;:&lt;sync_high?=0&gt;:&lt;sync_low?=0&gt;:&lt;one_high?=0&gt;:&lt;one_low?=0&gt;:&lt;zero_high?=0&gt;:&lt;zero_low?=0&gt;

*Arguments:*

- *group*: Group

   range: 1-4

- *device*: Device

   range: 1-3

- *state*: State

   range: 0-1

- *preset*: Preset number 1-8 or 0 for custom durations

   range: 0-8

- *sync_high*: Sync High duration (for Preset 0)

   optional. Default: 0

   range: -2147483648-32bits

- *sync_low*: Sync Low duration (for Preset 0)

   optional. Default: 0

   range: -2147483648-32bits

- *one_high*: One High duration (for Preset 0)

   optional. Default: 0

   range: -2147483648-32bits

- *one_low*: One Low duration (for Preset 0)

   optional. Default: 0

   range: -2147483648-32bits

- *zero_high*: Zero High duration (for Preset 0)

   optional. Default: 0

   range: -2147483648-32bits

- *zero_low*: Zero Low duration (for Preset 0)

   optional. Default: 0

   range: -2147483648-32bits


### **samsung**
Samsung IR code. 32 bits

*Type:* IR

*Signature:* samsung:&lt;address&gt;:&lt;command&gt;

*Arguments:*

- *address*: Customer code

   range: 0-8bits

- *command*: Command code

   range: 0-8bits


### **samsung36**
Samsumg36 IR code.  It transmits the address and command in two packets separated by a “space”.

*Type:* IR

*Signature:* samsung36:&lt;address&gt;:&lt;command&gt;

*Arguments:*

- *address*: Address to send

   range: 0-16bits

- *command*: Samsung36 command to send

   range: 0-1048575


### **sony**
Sony IR code

*Type:* IR

*Signature:* sony:&lt;data&gt;:&lt;nbits?=12&gt;

*Arguments:*

- *data*: Code to send

   range: 0-32bits

- *nbits*: Number of bits to send (12, 15 or 20)

   optional. Default: 12

   range: 0-20

   values: [12, 15, 20]


### **toshiba_ac**
Toshiba AC IR code

*Type:* IR

*Signature:* toshiba_ac:&lt;rc_code_1&gt;:&lt;rc_code_2?=0&gt;

*Arguments:*

- *rc_code_1*: Remote control code

   range: 0-48bits

- *rc_code_2*: Secondary remote control code. Some code are sent in two parts

   optional. Default: 0

   range: 0-48bits

