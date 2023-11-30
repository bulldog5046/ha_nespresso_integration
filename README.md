<a href="https://www.buymeacoffee.com/bulldog5046" target="_blank"><img src="https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png" alt="Buy Me A Coffee" style="height: 41px !important;width: 174px !important;box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;-webkit-box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;" ></a>


# Nespresso

Nespresso Bluetooth integration for Home Assistant.

Originally intended to be a fork of the work from tikismoke but has morphed significantly and the original work is no longer under development i've decided to create a new project home.

Thank you to tikismoke and all those before him who helped reverse engineer the protocols.

https://github.com/tikismoke/home-assistant-nespressoble

This project is still a work in progress

# Features
* Native configuration flow for Home Assistant
* Device discovery
* Direct pairing/auth (No need to extract auth_key from mobile app)
* Reworked to use the native Home Assistant bleak bluetooth library

# Requirements
* The integration expects the machine to be in a factory reset state and ready for a new device to be paired.

# Examples
## Basic button
![Basic Card](examples/Screenshot%202023-11-14%20233944.png)

A basic button card can directly call the service with the data provided if you only want a simple button option, or if you want a dashboard with various button options.

```
show_name: true
show_icon: true
type: button
tap_action:
  action: toggle
entity: sensor.expert_milk_d1e1037c4a9d_always_1
hold_action:
  action: call-service
  service: nespresso.coffee
  target: {}
  data:
    brew_temp: Medium
    brew_type: Lungo
show_state: false
icon: mdi:coffee
name: Brew Americano
```

## Selectable Options
![Example Card](examples/Screenshot%202023-11-14%20232456.png)

Create two helpers for the dropdown lists with the values available in the machines.BrewType and machines.Temprature enums. Low or mixed case values on the dropdown for appearance. The text values will be converted up uppercase within the service call.

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

Create the card.

```
type: entities
title: Coffee Maker Controls
entities:
  - entity: input_select.brew_type
  - entity: input_select.brew_temp
  - type: button
    tap_action:
      action: call-service
      service: script.brew_coffee
    name: Brew Coffee
```

## Custom recipes
![Custom Recipes](examples/Screenshot%202023-11-15%20142912.png)

The service supports optional configuration parameters to allow you to create your own ideal recipe. When adding the call service to a button card you can define the quantity of coffee and water in mililiters to dispense.

```
show_name: true
show_icon: true
type: button
tap_action:
  action: call-service
  service: nespresso.coffee
  target: {}
  data:
    coffee_ml: 123
    water_ml: 69
    brew_temp: Medium
entity: sensor.expert_milk_d1e1037c4a9d_always_1
name: Custom Recipe
icon_height: 50px
show_state: false
icon: mdi:coffee-outline
```

## Caps Counter
![Caps Counter](examples/Screenshot%202023-11-18%20205241.png)

Reading/writing the caps counter is supported. Be aware that the counter doesn't update until the next time the machine is polled for sensor data (every 5 minutes). 

Example card
```
type: vertical-stack
cards:
  - show_state: true
    show_name: false
    camera_view: auto
    type: picture-entity
    entity: sensor.expert_milk_d1e1037c4a9d_caps_number
    image: /local/NespressoCaps.png
  - type: entities
    entities:
      - entity: input_number.caps_counter
        name: Set New Counter Total
      - type: call-service
        name: Update Capsule Count
        action_name: Set Counter
        service: script.update_capsule_count
    show_header_toggle: false
```

**scripts.yaml**
```
update_capsule_count:
  alias: Update Capsule Count
  sequence:
    - service: nespresso.caps
      data:
        caps: "{{ states('input_number.caps_counter') }}"
  mode: single
```

# Troubleshooting

While working on this project I've observed some quirks with Home Assistant and Bluetooth. In an effort to help people resolve their own problems, here are the most common things i've come across.

1. **The machine only brews once**

This is an easy one. The lid must be cycled between brew events when controlled over bluetooth.

2. **The pairing process fails**

I've seen various combinations of systems and bluetooth dongles that seem to fail the standard bluetooth pairing. The easiest way to verify this on your system is to run bluetoothctl and manually attempt to pair. You should see the same error in the Home Assistant logs.

![bluetoothctl failing](examples/Screenshot%202023-11-15%20180414.png)

Frustratingly, this issue may go away if you try the same dongle on a different system. I can only assume its a driver related issue.

3. **The device is setup but there are no entities**

Something went wrong when installing the new auth_key. Delete the device from Home Assistant, factory reset the machine and try again.
