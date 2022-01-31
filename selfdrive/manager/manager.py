#!/usr/bin/env python3
import datetime
import os
import signal
import subprocess
import sys
import traceback
from typing import List, Tuple, Union

import cereal.messaging as messaging
import selfdrive.sentry as sentry
from common.basedir import BASEDIR
from common.params import Params, ParamKeyType
from common.text_window import TextWindow
from selfdrive.boardd.set_time import set_time
from selfdrive.hardware import HARDWARE, PC, EON
from selfdrive.hardware.eon.apk import (pm_apply_packages, update_apks)
from selfdrive.manager.helpers import unblock_stdout
from selfdrive.manager.process import ensure_running
from selfdrive.manager.process_config import managed_processes
from selfdrive.athena.registration import register, UNREGISTERED_DONGLE_ID
from selfdrive.swaglog import cloudlog, add_file_handler
from selfdrive.version import is_dirty, get_commit, get_version, get_origin, get_short_branch, \
                              terms_version, training_version


sys.path.append(os.path.join(BASEDIR, "pyextra"))


def manager_init() -> None:
  # update system time from panda
  set_time(cloudlog)

  # save boot log
  # subprocess.call("./bootlog", cwd=os.path.join(BASEDIR, "selfdrive/loggerd"))

  params = Params()
  params.clear_all(ParamKeyType.CLEAR_ON_MANAGER_START)

  default_params: List[Tuple[str, Union[str, bytes]]] = [
    ("CompletedTrainingVersion", "0"),
    ("HasAcceptedTerms", "0"),
    ("OpenpilotEnabledToggle", "1"),
    ("IsMetric", "1"),
    ("EndToEndToggle", "1"),
    ("IsOpenpilotViewEnabled", "0"),
    ("OpkrAutoShutdown", "2"),
    ("OpkrForceShutdown", "5"),
    ("OpkrAutoScreenOff", "0"),
    ("OpkrUIBrightness", "0"),
    ("OpkrUIVolumeBoost", "0"),
    ("OpkrEnableDriverMonitoring", "1"),
    ("OpkrEnableLogger", "0"),
    ("OpkrEnableUploader", "0"),
    ("OpkrEnableGetoffAlert", "0"),
    ("OpkrAutoResume", "1"),
    ("OpkrVariableCruise", "1"),
    ("OpkrLaneChangeSpeed", "45"),
    ("OpkrAutoLaneChangeDelay", "0"),
    ("OpkrSteerAngleCorrection", "0"),
    ("PutPrebuiltOn", "1"),
    ("LdwsCarFix", "0"),
    ("LateralControlMethod", "2"),
    ("CruiseStatemodeSelInit", "1"),
    ("InnerLoopGain", "35"),
    ("OuterLoopGain", "20"),
    ("TimeConstant", "14"),
    ("ActuatorEffectiveness", "20"),
    ("Scale", "1500"),
    ("LqrKi", "15"),
    ("DcGain", "270"),
    ("PidKp", "25"),
    ("PidKi", "50"),
    ("PidKd", "150"),
    ("PidKf", "7"),
    ("CameraOffsetAdj", "60"),
    ("PathOffsetAdj", "0"),
    ("SteerRatioAdj", "1550"),
    ("SteerRatioMaxAdj", "1750"),
    ("SteerActuatorDelayAdj", "20"),
    ("SteerRateCostAdj", "35"),
    ("SteerLimitTimerAdj", "100"),
    ("TireStiffnessFactorAdj", "100"),
    ("SteerMaxBaseAdj", "384"),
    ("SteerMaxAdj", "384"),
    ("SteerDeltaUpBaseAdj", "3"),
    ("SteerDeltaUpAdj", "3"),
    ("SteerDeltaDownBaseAdj", "7"),
    ("SteerDeltaDownAdj", "7"),
    ("SteerMaxvAdj", "10"),
    ("OpkrBatteryChargingControl", "1"),
    ("OpkrBatteryChargingMin", "70"),
    ("OpkrBatteryChargingMax", "80"),
    ("LeftCurvOffsetAdj", "0"),
    ("RightCurvOffsetAdj", "0"),
    ("DebugUi1", "0"),
    ("DebugUi2", "0"),
    ("LongLogDisplay", "0"),
    ("OpkrBlindSpotDetect", "1"),
    ("OpkrMaxAngleLimit", "90"),
    ("OpkrSpeedLimitOffset", "0"),
    ("OpkrLiveSteerRatio", "1"),
    ("OpkrVariableSteerMax", "0"),
    ("OpkrVariableSteerDelta", "0"),
    ("FingerprintTwoSet", "0"),
    ("OpkrDrivingRecord", "0"),
    ("OpkrTurnSteeringDisable", "0"),
    ("CarModel", ""),
    ("OpkrHotspotOnBoot", "0"),
    ("OpkrSSHLegacy", "1"),
    ("CruiseOverMaxSpeed", "0"),
    ("JustDoGearD", "0"),
    ("LanelessMode", "2"),
    ("ComIssueGone", "1"),
    ("MaxSteer", "408"),
    ("MaxRTDelta", "112"),
    ("MaxRateUp", "3"),
    ("MaxRateDown", "7"),
    ("SteerThreshold", "150"),
    ("RecordingCount", "100"),
    ("RecordingQuality", "1"),
    ("CruiseGapAdjust", "0"),
    ("AutoEnable", "1"),
    ("CruiseAutoRes", "0"),
    ("AutoResOption", "0"),
    ("AutoResCondition", "0"),
    ("SteerWindDown", "0"),
    ("OpkrMonitoringMode", "0"),
    ("OpkrMonitorEyesThreshold", "45"),
    ("OpkrMonitorNormalEyesThreshold", "45"),
    ("OpkrMonitorBlinkThreshold", "35"),
    ("MadModeEnabled", "1"),
    ("WhitePandaSupport", "0"),
    ("SteerWarningFix", "0"),
    ("OpkrRunNaviOnBoot", "0"),
    ("CruiseGap1", "10"),
    ("CruiseGap2", "12"),
    ("CruiseGap3", "14"),
    ("CruiseGap4", "16"),
    ("DynamicTR", "2"),
    ("OpkrBattLess", "0"),
    ("LCTimingFactorUD", "1"),
    ("LCTimingFactor30", "10"),
    ("LCTimingFactor60", "20"),
    ("LCTimingFactor80", "70"),
    ("LCTimingFactor110", "100"),
    ("OpkrUIBrightnessOff", "10"),
    ("LCTimingFactorEnable", "1"),
    ("AutoEnableSpeed", "3"),
    ("SafetyCamDecelDistGain", "0"),
    ("OpkrLiveTunePanelEnable", "0"),
    ("RadarLongHelper", "1"),
    ("GitPullOnBoot", "0"),
    ("LiveSteerRatioPercent", "-5"),
    ("StoppingDistAdj", "0"),
    ("ShowError", "1"),
    ("AutoResLimitTime", "0"),
    ("VCurvSpeed30", "40"),
    ("VCurvSpeed50", "50"),
    ("VCurvSpeed70", "65"),
    ("VCurvSpeed90", "85"),
    ("VCurvSpeedUD", "1"),
    ("OCurvSpeed30", "35"),
    ("OCurvSpeed40", "45"),
    ("OCurvSpeed50", "60"),
    ("OCurvSpeed60", "70"),
    ("OCurvSpeed70", "80"),
    ("OCurvSpeedUD", "1"),
    ("OSMCustomOffset40", "0"),
    ("OSMCustomOffset50", "15"),
    ("OSMCustomOffset60", "12"),
    ("OSMCustomOffset70", "10"),
    ("OSMCustomOffset90", "5"),
    ("OSMCustomOffsetUD", "1"),
    ("StockNaviSpeedEnabled", "0"),
    ("OPKRNaviSelect", "2"),
    ("dp_atl", "1"),
    ("E2ELong", "0"),
    ("GoogleMapEnabled", "0"),
    ("OPKRServer", "0"),
    ("OPKRMapboxStyleSelect", "0"),
    ("IgnoreCANErroronISG", "0"),
    ("RESCountatStandstill", "20"),
    ("OpkrSpeedLimitOffsetOption", "0"),
    ("OpkrSpeedLimitSignType", "0"),
    ("StockLKASEnabled", "1"),
    ("SpeedLimitDecelOff", "0"),
    ("CurvDecelOption", "2"),
    ("FCA11Message", "0"),
    ("StandstillResumeAlt", "0"),
    ("MapboxEnabled", "0"),
    ("AutoRESDelay", "0"),
    ("UseRadarTrack", "0"),
    ("RadarDisable", "0"),
  ]
  if not PC:
    default_params.append(("LastUpdateTime", datetime.datetime.utcnow().isoformat().encode('utf8')))

  if params.get_bool("RecordFrontLock"):
    params.put_bool("RecordFront", True)

  if not params.get_bool("DisableRadar_Allow"):
    params.delete("DisableRadar")

  # set unset params
  for k, v in default_params:
    if params.get(k) is None:
      params.put(k, v)

  # is this dashcam?
  if os.getenv("PASSIVE") is not None:
    params.put_bool("Passive", bool(int(os.getenv("PASSIVE", "0"))))

  if params.get("Passive") is None:
    raise Exception("Passive must be set to continue")

  if EON:
    update_apks(show_spinner=True)
  # Create folders needed for msgq
  try:
    os.mkdir("/dev/shm")
  except FileExistsError:
    pass
  except PermissionError:
    print("WARNING: failed to make /dev/shm")

  # set version params
  params.put("Version", get_version())
  params.put("TermsVersion", terms_version)
  params.put("TrainingVersion", training_version)
  params.put("GitCommit", get_commit(default=""))
  params.put("GitBranch", get_short_branch(default=""))
  params.put("GitRemote", get_origin(default=""))

  # set dongle id
  reg_res = register(show_spinner=True)
  if reg_res:
    dongle_id = reg_res
  elif not reg_res:
    dongle_id = "maintenance"
  else:
    serial = params.get("HardwareSerial")
    raise Exception(f"Registration failed for device {serial}")
  os.environ['DONGLE_ID'] = dongle_id  # Needed for swaglog

  if not is_dirty():
    os.environ['CLEAN'] = '1'

  # init logging
  sentry.init(sentry.SentryProject.SELFDRIVE)
  cloudlog.bind_global(dongle_id=dongle_id, version=get_version(), dirty=is_dirty(),
                       device=HARDWARE.get_device_type())

  # opkr
  if os.path.isfile('/data/log/error.txt'):
    os.remove('/data/log/error.txt')
  if os.path.isfile('/data/log/can_missing.txt'):
    os.remove('/data/log/can_missing.txt')
  if os.path.isfile('/data/log/can_timeout.txt'):
    os.remove('/data/log/can_timeout.txt')

  # ensure shared libraries are readable by apks
  if EON:
    os.chmod(BASEDIR, 0o755)
    os.chmod("/dev/shm", 0o777)
    os.chmod(os.path.join(BASEDIR, "cereal"), 0o755)
    os.chmod(os.path.join(BASEDIR, "cereal", "libmessaging_shared.so"), 0o755)

  os.system("/data/openpilot/selfdrive/assets/addon/script/gitcommit.sh")

def manager_prepare() -> None:
  for p in managed_processes.values():
    p.prepare()


def manager_cleanup() -> None:
  if EON:
    pm_apply_packages('disable')

  # send signals to kill all procs
  for p in managed_processes.values():
    p.stop(block=False)

  # ensure all are killed
  for p in managed_processes.values():
    p.stop(block=True)

  cloudlog.info("everything is dead")


def manager_thread() -> None:
  cloudlog.bind(daemon="manager")
  cloudlog.info("manager start")
  cloudlog.info({"environ": os.environ})

  params = Params()

  ignore: List[str] = []
  if params.get("DongleId", encoding='utf8') in (None, UNREGISTERED_DONGLE_ID):
    ignore += ["manage_athenad", "uploader"]
  if os.getenv("NOBOARD") is not None:
    ignore.append("pandad")
  ignore += [x for x in os.getenv("BLOCK", "").split(",") if len(x) > 0]

  if EON:
    pm_apply_packages('enable')

  ensure_running(managed_processes.values(), started=False, not_run=ignore)

  started_prev = False
  sm = messaging.SubMaster(['deviceState'])
  pm = messaging.PubMaster(['managerState'])

  while True:
    sm.update()
    not_run = ignore[:]

    started = sm['deviceState'].started
    driverview = params.get_bool("IsDriverViewEnabled")
    ensure_running(managed_processes.values(), started, driverview, not_run)

    # trigger an update after going offroad
    if started_prev and not started and 'updated' in managed_processes:
      os.sync()
      managed_processes['updated'].signal(signal.SIGHUP)

    started_prev = started

    running = ' '.join("%s%s\u001b[0m" % ("\u001b[32m" if p.proc.is_alive() else "\u001b[31m", p.name)
                       for p in managed_processes.values() if p.proc)
    print(running)
    cloudlog.debug(running)

    # send managerState
    msg = messaging.new_message('managerState')
    msg.managerState.processes = [p.get_process_state_msg() for p in managed_processes.values()]
    pm.send('managerState', msg)

    # Exit main loop when uninstall/shutdown/reboot is needed
    shutdown = False
    for param in ("DoUninstall", "DoShutdown", "DoReboot"):
      if params.get_bool(param):
        shutdown = True
        params.put("LastManagerExitReason", param)
        cloudlog.warning(f"Shutting down manager - {param} set")

    if shutdown:
      break


def main() -> None:
  prepare_only = os.getenv("PREPAREONLY") is not None

  manager_init()

  # Start UI early so prepare can happen in the background
  if not prepare_only:
    managed_processes['ui'].start()

  manager_prepare()

  if prepare_only:
    return

  # SystemExit on sigterm
  signal.signal(signal.SIGTERM, lambda signum, frame: sys.exit(1))

  try:
    manager_thread()
  except Exception:
    traceback.print_exc()
    sentry.capture_exception()
  finally:
    manager_cleanup()

  params = Params()
  if params.get_bool("DoUninstall"):
    cloudlog.warning("uninstalling")
    HARDWARE.uninstall()
  elif params.get_bool("DoReboot"):
    cloudlog.warning("reboot")
    HARDWARE.reboot()
  elif params.get_bool("DoShutdown"):
    cloudlog.warning("shutdown")
    HARDWARE.shutdown()


if __name__ == "__main__":
  unblock_stdout()

  try:
    main()
  except Exception:
    add_file_handler(cloudlog)
    cloudlog.exception("Manager failed to start")

    # Show last 3 lines of traceback
    error = traceback.format_exc(-3)
    error = "Manager failed to start\n\n" + error
    with TextWindow(error) as t:
      t.wait_for_exit()

    raise

  # manual exit because we are forked
  sys.exit(0)
