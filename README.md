# zlac8015d_can_bringup
# zlac_can_bringup

ZLAC8015D モータドライバを使用した対向二輪型移動ロボット用の **ROS 2 起動・設定パッケージ**です。`zlac8015d_hardware` の `ros2_control` ハードウェアプラグインを読み込み、左右車輪の速度指令、関節状態、オドメトリを扱えるようにします。

**起動コマンド**

```bash
ros2 launch zlac_can_bringup zlac_can_bringup.launch.py
```

## 動作環境

- Ubuntu 22.04 / ROS 2 Humble
- `zlac8015d_hardware` パッケージ（同じROS 2ワークスペースに配置）
- `ros2_control` / `ros2_controllers`
- `controller_manager` / `joint_state_broadcaster` / `diff_drive_controller`
- `robot_state_publisher` / `launch_ros`
- SocketCAN インターフェース（初期設定 `can0`）と ZLAC8015D モータドライバ

ROS 2 がインストール済みで、コントローラ等が未導入の場合の例：

```bash
sudo apt update
sudo apt install ros-humble-ros2-control ros-humble-ros2-controllers \
  ros-humble-robot-state-publisher can-utils
```

## ファイル構成

```text
zlac_can_bringup/
├── CMakeLists.txt
├── package.xml
├── launch/
│   └── zlac_can_bringup.launch.py
├── config/
│   └── controllers.yaml
└── urdf/
    ├── orange_go_2025.urdf
    └── orange_go_2025_before_ladrc_cmdvel.urdf
```

- `launch/zlac_can_bringup.launch.py`：ドライバとROS 2コントローラ群を起動。
- `config/controllers.yaml`：制御周期、差動二輪コントローラ、オドメトリの設定。
- `urdf/orange_go_2025.urdf`：車輪ジョイント、`ros2_control` インターフェース、CAN通信、LADRCパラメータなどの現行設定。
- `urdf/orange_go_2025_before_ladrc_cmdvel.urdf`：過去の設定を残した比較・バックアップファイル。通常のlaunchでは**読み込まれません**。

## インストールとビルド

`~/ros2_ws/src/` 以下に本パッケージと `zlac8015d_hardware` パッケージを配置してください。ZIPの展開フォルダ名に `-devel-ADRC` の接尾辞があっても、`package.xml` で定義されたパッケージ名は `zlac_can_bringup` です。

```bash
source /opt/ros/humble/setup.bash
cd ~/ros2_ws
colcon build --packages-select zlac8015d_hardware zlac_can_bringup --symlink-install
source install/setup.bash
```

`can0` の存在・状態を確認します。

```bash
ip -details link show can0
```

CAN インターフェースが未設定の場合は、機器に適したビットレートで有効化してください。このパッケージはCANインターフェースの作成やバスの物理接続復旧を行いません。

## 起動方法

```bash
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
ros2 launch zlac_can_bringup zlac_can_bringup.launch.py
```

launchは次のノード・コントローラを起動します。

| 要素 | 役割 |
| --- | --- |
| `robot_state_publisher` | URDFからロボットのリンク・ジョイント情報を公開 |
| `controller_manager` (`ros2_control_node`) | `zlac8015d_hardware` プラグインと制御ループを実行 |
| `joint_state_broadcaster` | 車輪ジョイントの状態を `/joint_states` に公開 |
| `diff_drive_controller` | `/cmd_vel` から左右の車輪角速度指令を生成し、オドメトリを公開 |

停止する場合は起動ターミナルで `Ctrl+C` を押します。

## 主なROS 2インターフェース

| トピック | データ型・内容 |
| --- | --- |
| `/cmd_vel` | `geometry_msgs/msg/Twist`：目標並進速度 `linear.x` [m/s] と角速度 `angular.z` [rad/s] |
| `/joint_states` | `sensor_msgs/msg/JointState`：左右の車輪の位置・速度・effort |
| `/odom` | `nav_msgs/msg/Odometry`：車輪オドメトリ |
| `/tf` | `odom` → `base_footprint` などのTF（設定に基づく） |

`/cmd_vel` への接続はlaunch内の `diff_drive_controller/cmd_vel_unstamped` からのリマッピングで行っています。`use_stamped_vel: false` の設定により、タイムスタンプなしの `Twist` を使用します。

動作確認例（別ターミナル）：

```bash
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash

ros2 control list_controllers
ros2 topic echo /joint_states
ros2 topic echo /odom
```

モータ指令の検証は、車輪を浮かせるなど安全を確保した状態で実施してください。

## 制御パラメータ

### `config/controllers.yaml`

添付ファイルの設定値は以下です。

| 項目 | 値 | 内容 |
| --- | --- | --- |
| `controller_manager.update_rate` | `200` | 制御更新周期 [Hz] |
| `wheel_separation` | `0.354` | 車輪間距離 [m] |
| `wheel_radius` | `0.064` | 車輪半径 [m] |
| `publish_rate` | `50.0` | オドメトリなどの公開周期 [Hz] |
| `open_loop` | `false` | 実測状態を使用 |
| `position_feedback` | `true` | エンコーダ位置フィードバックを使用 |
| `enable_odom_tf` | `true` | オドメトリTFを配信 |
| `odom_frame_id` | `odom` | オドメトリ座標系 |
| `base_frame_id` | `base_footprint` | ロボット基準座標系 |
| `use_stamped_vel` | `false` | `/cmd_vel` は `Twist` 形式 |

車輪名は `left_wheel_joint` / `right_wheel_joint` です。**URDFとYAMLの車輪名・寸法が一致している必要があります。**

### `urdf/orange_go_2025.urdf`

`ros2_control` の `<hardware>` に以下を指定しています。

```xml
<plugin>zlac8015d_hardware/Zlac8015dSystemHardware</plugin>
<param name="can_interface">can0</param>
<param name="node_id">1</param>
<param name="control_mode">ladrc_torque</param>
<param name="ladrc_b0_left">20.0</param>
<param name="ladrc_b0_right">20.0</param>
<param name="ladrc_wc">5.0</param>
<param name="ladrc_wo">20.0</param>
<param name="current_limit_a">8.0</param>
<param name="current_rate_limit_a_per_s">20.0</param>
<param name="feedback_timeout_ms">30.0</param>
```

制御方式は `control_mode` によって切り替えます。

- **`velocity`**：ドライバ内蔵の速度制御を使用。
- **`ladrc_torque`**：左右車輪の速度追従用LADRCから電流を指令。初期設定はこちらです。

どちらの場合も、`diff_drive_controller` からハードウェアへは**車輪角速度指令**が渡されます。`ladrc_torque` の電流指令への変換は `zlac8015d_hardware` 内部で行われます。パラメータ変更後は、launchを再起動してください。

## CAN通信とエンコーダ

CANopen ノードID `1` の場合、ハードウェア側は主に次のCANフレームを扱います。

| CAN ID | 内容 |
| --- | --- |
| `0x181` | 左右の実測角速度 |
| `0x281` | 左右の実測モータ電流 |
| `0x381` | 左右のエンコーダ位置 |
| `0x201` | LADRCモードの電流指令 |
| `0x301` | 速度制御モードの角速度指令 |

受信したエンコーダは起動時の値を原点とする相対値として扱われます。**再起動すると車輪位置およびそこから計算されるオドメトリの連続性が失われる可能性があります。**

## CAN通信断からの自動再起動（任意）

この**最初に添付されたbringup ZIPには自動再起動スクリプトは含まれません**。別途作成・動作確認済みの `can_launch_watchdog.py` をUbuntu PCに配置することで、launchを監視して再起動できます。

```bash
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
python3 ~/can_launch_watchdog.py
```

制御モードが `velocity` などで `/tmp/ladrc_track_200hz.csv` を生成しない場合は、CSV更新監視を無効にしてください。

```bash
python3 ~/can_launch_watchdog.py --log-file ""
```

watchdog使用時は、そのプログラムがlaunchを起動するため、**別途 `ros2 launch ...` を同時実行しないでください**。これはオプションであり、本パッケージの基本動作に必須ではありません。

## トラブルシューティング

| 症状 | 確認する項目 |
| --- | --- |
| `can0` が見つからない | `ip -details link show can0`、CANアダプタ、インターフェース名 |
| `ros2_control` が初期化できない | `zlac8015d_hardware` のビルドと読み込み、URDFのplugin名 |
| `diff_drive_controller` が起動しない | `ros2 control list_controllers`、ジョイント名、YAML設定 |
| `/joint_states` が更新されない | CAN配線・電源、PDO受信、`candump can0` |
| ロボットの走行方向がおかしい | 左右の接続、モータ極性、車輪名、符号設定 |
| `/odom` が不連続になる | ハードウェアの再起動・エンコーダ原点の再設定 |

## 安全上の注意

- 本パッケージはモータを有効化するため、起動前に非常停止手段を確保してください。
- 通信断・電源断の際の安全停止は、ソフトウェアだけでなくドライバ設定・ハードウェアで確保してください。
- モータやエンコーダの配線、車輪寸法、CANノードIDが異なる機体には、設定を変更してから使用してください。
- 同じCANopenノードに対し、bringupと独立した同定プログラムを同時に動かさないでください。

## ライセンス

添付された `package.xml` のライセンス欄は `TODO` のままです。GitHubで公開する際は権利関係を確認し、適切な `LICENSE` ファイルとライセンス表記を追加してください。
