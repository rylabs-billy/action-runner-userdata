#!/bin/bash

# input validation and error handling
_error_msg() {
  case "${1}" in
    repo_err)
      echo -e "::error title=missing input::repository scope requires 'owner' and 'repo' inputs\n" ;;
    org_err)
      echo -e "::error title=missing input::organization scope requires 'org' input\n" ;;
    input_err)
      echo -e "::error title=invalid input::scope requires input values of 'repository' or 'organization'\n" ;;
    config_err)
      echo -e "::error title=invalid cloud-config::yaml formatting error.\n" ;;
    github_err)
      echo -e "::error title=api error::github api returned an error response.\n" ;;
  esac
  exit 1
}

_error_check() {
  case "${1}" in
    cloud_config)
      echo "${2}" | base64 -d > test.yml
      cloud-init schema -c test.yml --annotate > /dev/null || _error_msg config_err ;;
    github_api)
      [ "$?" != "0" ] && { echo "${2}" | awk -F'}' '{print $2}'; _error_msg github_err; } ;;
  esac
}

# set github variables from inputs
_set_path() {
  if [ "${1}" == "repo" ]
  then
    path="${OWNER}/${REPO}"
    _name="${repo}"
  else
    path="${ORG}"
    _name="${ORG}"
  fi
  github_url="$GITHUB_SERVER_URL/${path}"
  github_api="/${1}s/${path}/actions/runners"  
  _name="${_name}"
}

runner_scope(){
  if [ "${SCOPE}" == "repository" ]
  then
    [ -n "${OWNER}" ] && [ -n "${REPO}" ] && _set_path repo || _error_msg repo_err
  elif [ "${SCOPE}" == "organization" ]
  then
    [ -n "${ORG}" ] && _set_path org || _error_msg org_err
  else
    _error_msg input_err
  fi
}

# runner config options
config_opts() {
  opts=()

  if [ ! -n "${NAME}" ]
  then
    local date=$(date '+%Y-%m-%d-%H%M%S')
    name="${_name}-${date}"
  else
    local replace="--replace"
    name="${NAME}"
  fi
  echo "runner-name=$name" >> $GITHUB_OUTPUT
  opts+=("--name ${name}")

  [ -n "{RUNNERGROUP}" ] && opts+=("--runnergroup ${RUNNERGROUP}")

  [ -n "${LABELS}" ] && opts+=("--labels ${LABELS}")

  [ -n "${WORK}" ] && opts+=("--work ${WORK}")

  [ "${EPHEMERAL}" == "true" ] && opts+=("--ephemeral")

  [ -n "${replace}" ] && opts+=("${replace}")

  options=$(echo "${opts[@]}")
}


# create runner registration token
runner_token() {
  response=$(gh api --method POST \
    -H "Accept: application/vnd.github+json" \
    -H "X-GitHub-Api-Version: 2022-11-28" \
    "${github_api}"/registration-token 2>&1)

  _error_check github_api "${response}"

  registration_token=$(echo "${response}" | jq -r .token)
  echo "::add-mask::${registration_token}"
}

cloud_config() {
  # encode cloud-init metadata
  local metadata=$(printf "%s\n" \
    "#cloud-config" \
    "package_update: true" \
    "package_upgrade: true" \
    "runcmd:" \
      "- mkdir actions-runner" \
      "- cd actions-runner" \
      "- curl -o actions-runner-linux-x64-2.300.2.tar.gz -L https://github.com/actions/runner/releases/download/v2.300.2/actions-runner-linux-x64-2.300.2.tar.gz" \
      "- echo 'ed5bf2799c1ef7b2dd607df66e6b676dff8c44fb359c6fedc9ebf7db53339f0c  actions-runner-linux-x64-2.300.2.tar.gz' | shasum -a 256 -c" \
      "- tar xzf ./actions-runner-linux-x64-2.300.2.tar.gz" \
      "- ./bin/installdependencies.sh" \
      "- export RUNNER_ALLOW_RUNASROOT='1'" \
      "- ./config.sh --unattended --url ${github_url} --token ${registration_token} ${options}" \
      "- ./run.sh")

  user_data=$(echo "${metadata}" | sed 's/- /  - /g' | base64 -w 0)
  _error_check cloud_config "${user_data}"

  echo "::add-mask::${user_data}"
  echo "user-data=$user_data" >> $GITHUB_OUTPUT
}

# main
runner_scope
config_opts
runner_token
cloud_config
