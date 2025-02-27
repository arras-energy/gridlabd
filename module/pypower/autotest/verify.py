def write_glm(glm,case):
    """Convert case data to glm asserts that verify results"""
    with open(glm,"w") as fh:
        for bus in case['bus']:
            print(f"""object assert
{{      
    parent pp_bus_{bus[0]:.0f};
    target Vm;
    relation ==;
    value {bus[7]:.3f};
    within ${{MRES}};
}}
object assert
{{
    parent pp_bus_{bus[0]:.0f};
    target Va;
    relation ==;
    value {bus[8]:.2f};
    within ${{ARES}};
}}
""",file=fh)
