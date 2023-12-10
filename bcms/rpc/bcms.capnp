@0x955ea5acce24dc79;

struct BCMSDeviceInfo {
    address  @0 :Text;
    name     @1 :Text;
    approved @2 :Bool;
    paired   @3 :Bool;
}

enum BCMSWorkingMode {
    any        @0;
    approved @1;
}

interface BCMS {
    list     @0 (onlyApproved :Bool) -> (devices :List(BCMSDeviceInfo), errors :List(Text));
    approve  @1 (address :Text) -> (status :Bool, errors :List(Text));
    remove   @2 (address :Text) -> (status :Bool, errors :List(Text));
    mode     @3 () -> (mode :BCMSWorkingMode);
    setMode  @4 (mode :BCMSWorkingMode) -> (status: Bool, errors :List(Text));
    pair     @5 (address :Text) -> (status :Bool, errors :List(Text));
    unpair   @6 (address :Text) -> (status :Bool, errors :List(Text));
    isPaired @7 (address :Text) -> (status :Bool, errors :List(Text));
}
