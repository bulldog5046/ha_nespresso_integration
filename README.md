# Nespresso

Nespresso Bluetooth integration for Home Assistant.

Originally intended to be a fork of the work from tikismoke but has morphed significantly and the original work is no longer under development i've decided to create a new project home.

Thank you to tikismoke and all those before him who helped reverse engineer the protocols.

https://github.com/tikismoke/home-assistant-nespressoble

This project is still a work in progress

# Features
* Native configuration flow for Hoem Assistant
* Device discovery
* Direct pairing/auth (No need to extract auth_key from mobile app)
* Reworked to use the native Home Assistant bleak bluetooth library

# Example
![Example Card](examples/Screenshot%202023-11-14%20232456.png)

Create two helpers for the dropdown lists with the values available in the machines.BrewType and machines.Temprature enums.

![Helpers](examples/Screenshot%202023-11-14%20233208.png)

Add the following to your scripts.yaml to wrap the input selectors with the service call.

**scripts.yaml**
```
brew_coffee:
  sequence:
    - service: nespresso.coffee
      data:
        brew_type: "{{ states('input_select.brew_type') }}"
        brew_temp: "{{ states('input_select.brew_temp') }}"
  alias: Brew Coffee
```
