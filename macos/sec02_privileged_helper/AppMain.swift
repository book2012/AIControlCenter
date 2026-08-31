import Foundation

// Process-only bootstrap. Service registration, authorization, XPC operations,
// key provisioning, and Production mutation are deliberately absent.
@main
struct AIControlCenterMain {
    static func main() {
        // The unsigned C3 application proves only that a native process can be
        // built and packaged. It confers no governance or Production authority.
    }
}
