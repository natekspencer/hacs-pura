[![Release](https://img.shields.io/github/v/release/natekspencer/hacs-pura?style=for-the-badge)](https://github.com/natekspencer/hacs-pura/releases)
[![Buy Me A Coffee/Beer](https://img.shields.io/badge/Buy_Me_A_☕/🍺-F16061?style=for-the-badge&logo=ko-fi&logoColor=white&labelColor=grey)](https://ko-fi.com/natekspencer)
[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)

![Downloads](https://img.shields.io/github/downloads/natekspencer/hacs-pura/total?style=flat-square)
![Latest Downloads](https://img.shields.io/github/downloads/natekspencer/hacs-pura/latest/total?style=flat-square)

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://brands.home-assistant.io/pura/dark_logo.png">
  <img alt="Pura logo" src="https://brands.home-assistant.io/pura/logo.png">
</picture>

# Pura for Home Assistant

Home Assistant integration for Pura smart fragrance diffusers.

# Installation

There are two main ways to install this custom component within your Home Assistant instance:

1. Using HACS (see https://hacs.xyz/ for installation instructions if you do not already have it installed):

   1. From within Home Assistant, click on the link to **HACS**
   2. Click on **Integrations**
   3. Click on the vertical ellipsis in the top right and select **Custom repositories**
   4. Enter the URL for this repository in the section that says _Add custom repository URL_ and select **Integration** in the _Category_ dropdown list
   5. Click the **ADD** button
   6. Close the _Custom repositories_ window
   7. You should now be able to see the _Pura_ card on the HACS Integrations page. Click on **INSTALL** and proceed with the installation instructions.
   8. Restart your Home Assistant instance and then proceed to the _Configuration_ section below.

2. Manual Installation:
   1. Download or clone this repository
   2. Copy the contents of the folder **custom_components/pura** into the same file structure on your Home Assistant instance
      - An easy way to do this is using the [Samba add-on](https://www.home-assistant.io/getting-started/configuration/#editing-configuration-via-sambawindows-networking), but feel free to do so however you want
   3. Restart your Home Assistant instance and then proceed to the _Configuration_ section below.

While the manual installation above seems like less steps, it's important to note that you will not be able to see updates to this custom component unless you are subscribed to the watch list. You will then have to repeat each step in the process. By using HACS, you'll be able to see that an update is available and easily update the custom component.

# Configuration

There is a config flow for this Pura integration. After installing the custom component:

1. Go to **Configuration**->**Integrations**
2. Click **+ ADD INTEGRATION** to setup a new integration
3. Search for **Pura** and click on it
4. You will be guided through the rest of the setup process via the config flow

---

## Support Me

I'm not employed by Pura, and provide this custom component purely for your own enjoyment and home automation needs.

If you don't already own a Pura diffuser, please consider using [my referal code (s3zjukz)](http://rwrd.io/s3zjukz) to get $6 off your first order of $50+ (as well as a tip to me in appreciation)!

If you already own a Pura diffuser and still want to donate, consider buying me a coffee ☕ (or beer 🍺) instead by using the link below:

<a href='https://ko-fi.com/natekspencer' target='_blank'><img height='35' style='border:0px;height:46px;' src='https://az743702.vo.msecnd.net/cdn/kofi3.png?v=0' border='0' alt='Buy Me a Coffee at ko-fi.com' />
