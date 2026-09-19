import QtQuick
import QtQuick.Layouts

import org.kde.kirigami as Kirigami
import org.kde.plasma.components as PlasmaComponents

ColumnLayout {
    id: section

    required property string title
    required property int remaining
    required property string resetText
    required property color accentColor

    spacing: Kirigami.Units.smallSpacing

    RowLayout {
        Layout.fillWidth: true

        PlasmaComponents.Label {
            text: section.title
            font.weight: Font.DemiBold
            Layout.fillWidth: true
        }

        PlasmaComponents.Label {
            text: section.remaining < 0 ? "—" : i18n("%1% remaining", section.remaining)
            color: section.accentColor
            font.weight: Font.Bold
        }
    }

    PlasmaComponents.ProgressBar {
        from: 0
        to: 100
        value: Math.max(0, section.remaining)
        Layout.fillWidth: true
        Accessible.name: i18n("%1 remaining", section.title)
        Accessible.description: section.remaining < 0
            ? i18n("Unavailable")
            : i18n("%1 percent", section.remaining)
    }

    PlasmaComponents.Label {
        text: i18n("Resets %1", section.resetText)
        color: Kirigami.Theme.disabledTextColor
        font: Kirigami.Theme.smallFont
    }
}
