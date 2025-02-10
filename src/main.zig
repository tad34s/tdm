const std = @import("std");
const cli = @import("cli.zig");
const yazap = @import("yazap");
const commands = @import("commands.zig");
const printError = @import("print_to_user.zig").printError;

const App = yazap.App;
const Arg = yazap.Arg;

pub fn main() u8 {
    var arena = std.heap.ArenaAllocator.init(std.heap.page_allocator);
    defer arena.deinit();

    const allocator = arena.allocator();

    var app: App = App.init(allocator, "tdm", null);
    defer app.deinit();
    _ = cli.configureCli(&app) catch |err| {
        printError("Failed creating CLI interface in yazap: {s}", err);
    };

    const matches = app.parseProcess() catch |err| {
        printError(null, err);
    };

    inline for (commands.commands) |subcommand| {
        if (matches.subcommandMatches(subcommand)) |sub_matches| {
            @field(commands, subcommand)(allocator, &sub_matches);
            return 0;
        }
    }

    return 0;

    //TODO:
    //
    // if (matches.subcommandMatches("git")) |_| {
    //     commands.git(app.process_args); // vymaz tdm, zbytek zavolej z tdm repa
    // }
    //
    //
}
