const ruleSetId = "pipeline_rules-";
const ruleFields = {
  required: ["monitor_tool", "order_no", "rule_type"],
  asset_id: [
    "set_value",
    "set_copy_from_flag",
    "override_flag",
    "ignore_empty_value_flag",
    "if_condition",
    "ignore_failure_flag",
  ],
  event_type: [
    "event_type_default",
    "event_type_field",
    "event_type_up_values",
    "event_type_down_values",
    "event_type_neutral_values",
  ],
  set: [
    "set_field",
    "set_value",
    "set_copy_from_flag",
    "override_flag",
    "ignore_empty_value_flag",
    "if_condition",
    "ignore_failure_flag",
  ],
  grok: [
    "grok_field",
    "grok_patterns",
    "grok_pattern_definitions",
    "ignore_missing_flag",
    "if_condition",
    "ignore_failure_flag",
  ],
  remove: ["remove_field", "ignore_missing_flag", "if_condition", "ignore_failure_flag"],
};

function onRuleTypeChange(e) {
  var fieldsetQuerySelector = "fieldset";
  if (Boolean(document.querySelector('div[id^="' + ruleSetId + '"]'))) {
    fieldsetQuerySelector = "div.inline-related#" + ruleSetId + e.target.id.split("-")[1] + " > fieldset";
  }

  const ruleTypeValue = e.target.value;
  const fieldset = document.querySelector(fieldsetQuerySelector);
  setFieldDisplay(ruleTypeValue, fieldset);
}

function setFieldDisplay(ruleType, fieldset) {
  fieldset.querySelectorAll("div.form-row").forEach((field) => {
    const requiredField = ruleFields.required.some((ruleFieldName) =>
      field.classList.contains("field-" + ruleFieldName)
    );
    const ruleField = ruleFields[ruleType].some((ruleFieldName) => field.classList.contains("field-" + ruleFieldName));
    if (requiredField || ruleField) {
      field.classList.remove("hide-field");
    } else {
      field.classList.add("hide-field");
    }
  });
}

$(document).ready(function (event) {
  const isMonitorToolPage = Boolean(document.querySelector('div[id^="' + ruleSetId + '"]'));
  if (isMonitorToolPage) {
    document.querySelectorAll('div.inline-related[id^="' + ruleSetId + '"]').forEach((element) => {
      const fieldset = element.querySelector("fieldset");
      var elementId = element.id.split("-")[1];
      if (elementId == "empty") {
        // INFO: for the template fieldset
        elementId = "__prefix__";
      }
      const ruleTypeValue = element.querySelector("select#id_" + ruleSetId + elementId + "-rule_type").value;
      setFieldDisplay(ruleTypeValue, fieldset);
    });
  } else {
    const fieldset = document.querySelector("fieldset");
    const ruleTypeValue = document.querySelector("select#id_rule_type").value;
    setFieldDisplay(ruleTypeValue, fieldset);
  }
});
